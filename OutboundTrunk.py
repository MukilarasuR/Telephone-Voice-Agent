import json
import logging
import os
import re
import subprocess
from dotenv import load_dotenv
from twilio.rest import Client

def get_env_var(var_name):
    value = os.getenv(var_name)
    if value is None:
        logging.error(f"Environment variable '{var_name}' not set.")
        exit(1)
    return value

def get_or_update_livekit_trunk(client, sip_uri):
    """Get existing LiveKit trunk or create/update it"""
    existing_trunks = client.trunking.v1.trunks.list()
    
    # Check if LiveKit trunk already exists
    for trunk in existing_trunks:
        if trunk.friendly_name == "LiveKit Trunk":
            logging.info(f"Found existing LiveKit Trunk: {trunk.sid}")
            
            # Check if origination URL exists
            origination_urls = trunk.origination_urls.list()
            existing_sip_url = None
            
            for url in origination_urls:
                if "livekit" in url.friendly_name.lower() or url.sip_url == sip_uri:
                    existing_sip_url = url
                    break
            
            if existing_sip_url:
                if existing_sip_url.sip_url != sip_uri:
                    # Update existing origination URL
                    existing_sip_url.update(sip_url=sip_uri)
                    logging.info(f"Updated existing origination URL with new SIP URI: {sip_uri}")
                else:
                    logging.info("SIP URI already configured correctly")
            else:
                # Add new origination URL
                trunk.origination_urls.create(
                    sip_url=sip_uri,
                    weight=1,
                    priority=1,
                    enabled=True,
                    friendly_name="LiveKit SIP URI",
                )
                logging.info(f"Added new origination URL: {sip_uri}")
            
            return trunk
    
    # If no existing trunk found, we have a problem with trial accounts
    logging.error("No existing LiveKit trunk found, but trial accounts can only have one trunk.")
    logging.error("Please delete existing trunk manually from Twilio Console or upgrade to paid account.")
    exit(1)

def delete_all_trunks_and_create_new(client, sip_uri):
    """Delete all existing trunks and create a new LiveKit trunk (use with caution)"""
    existing_trunks = client.trunking.v1.trunks.list()
    
    # Delete all existing trunks
    for trunk in existing_trunks:
        logging.info(f"Deleting trunk: {trunk.sid} ({trunk.friendly_name})")
        client.trunking.v1.trunks(trunk.sid).delete()
    
    # Create new trunk
    domain_name = f"livekit-trunk-{os.urandom(4).hex()}.pstn.twilio.com"
    trunk = client.trunking.v1.trunks.create(
        friendly_name="LiveKit Trunk",
        domain_name=domain_name,
    )
    
    # Add origination URL
    trunk.origination_urls.create(
        sip_url=sip_uri,
        weight=1,
        priority=1,
        enabled=True,
        friendly_name="LiveKit SIP URI",
    )
    
    logging.info(f"Created new LiveKit Trunk: {trunk.sid}")
    return trunk

def create_inbound_trunk(phone_number):
    """Create inbound trunk using LiveKit API directly"""
    try:
        # Check if LiveKit CLI is available
        result = subprocess.run(['lk', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            raise FileNotFoundError("LiveKit CLI not found")
        
        # Use CLI if available
        trunk_data = {
            "trunk": {
                "name": "Inbound LiveKit Trunk",
                "numbers": [phone_number]
            }
        }
        with open('inbound_trunk.json', 'w') as f:
            json.dump(trunk_data, f, indent=4)

        result = subprocess.run(
            ['lk', 'sip', 'inbound', 'create', 'inbound_trunk.json'],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            logging.error(f"Error executing command: {result.stderr}")
            return None

        match = re.search(r'ST_\w+', result.stdout)
        if match:
            inbound_trunk_sid = match.group(0)
            logging.info(f"Created inbound trunk with SID: {inbound_trunk_sid}")
            return inbound_trunk_sid
        else:
            logging.error("Could not find inbound trunk SID in output.")
            return None
            
    except FileNotFoundError:
        logging.warning("LiveKit CLI not found. Please install it or use LiveKit Cloud dashboard.")
        logging.info("To install LiveKit CLI:")
        logging.info("1. Via Chocolatey: choco install livekit-cli")
        logging.info("2. Via Scoop: scoop install livekit-cli")
        logging.info("3. Download from: https://github.com/livekit/livekit-cli/releases")
        logging.info("4. Or configure SIP trunk manually in LiveKit Cloud dashboard")
        return None

def create_dispatch_rule(trunk_sid):
    dispatch_rule_data = {
        "name": "Inbound Dispatch Rule",
        "trunk_ids": [trunk_sid],
        "rule": {
            "dispatchRuleIndividual": {
                "roomPrefix": "call-"
            }
        }
    }
    with open('dispatch_rule.json', 'w') as f:
        json.dump(dispatch_rule_data, f, indent=4)

    result = subprocess.run(
        ['lk', 'sip', 'dispatch-rule', 'create', 'dispatch_rule.json'],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        logging.error(f"Error executing command: {result.stderr}")
        return

    logging.info(f"Dispatch rule created: {result.stdout}")

def main():
    load_dotenv()
    logging.basicConfig(level=logging.INFO)

    account_sid = get_env_var("TWILIO_ACCOUNT_SID")
    auth_token = get_env_var("TWILIO_AUTH_TOKEN")
    phone_number = get_env_var("PHONE_NUMBER")
    sip_uri = get_env_var("LIVEKIT_SIP_URI")

    client = Client(account_sid, auth_token)

    # Choose one of the following options:
    
    # Option 1: Use existing trunk and update if needed (RECOMMENDED)
    livekit_trunk = get_or_update_livekit_trunk(client, sip_uri)
    
    # Option 2: Delete all trunks and create new one (CAUTION: This will delete ALL your trunks)
    # Uncomment the line below and comment out the line above if you want to use this option
    # livekit_trunk = delete_all_trunks_and_create_new(client, sip_uri)

    # Continue with inbound trunk creation
    inbound_trunk_sid = create_inbound_trunk(phone_number)
    if inbound_trunk_sid:
        create_dispatch_rule(inbound_trunk_sid)

if __name__ == "__main__":
    main()








# import json
# import logging
# import os
# import re
# import subprocess
# from dotenv import load_dotenv
# from twilio.rest import Client

# def get_env_var(var_name):
#     value = os.getenv(var_name)
#     if value is None:
#         logging.error(f"Environment variable '{var_name}' not set.")
#         exit(1)
#     return value

# def get_or_update_livekit_trunk(client, sip_uri):
#     """Get existing trunk and update it for LiveKit use"""
#     existing_trunks = client.trunking.v1.trunks.list()
    
#     if not existing_trunks:
#         logging.error("No existing trunks found.")
#         exit(1)
    
#     # List all existing trunks
#     logging.info("Found existing trunks:")
#     for i, trunk in enumerate(existing_trunks):
#         logging.info(f"  {i+1}. SID: {trunk.sid}, Name: {trunk.friendly_name}")
    
#     # Use the first trunk (since trial accounts can only have one)
#     trunk = existing_trunks[0]
#     logging.info(f"Using trunk: {trunk.sid} ({trunk.friendly_name})")
    
#     # Update the trunk name to LiveKit Trunk
#     trunk.update(friendly_name="LiveKit Trunk")
#     logging.info("Updated trunk name to 'LiveKit Trunk'")
    
#     # Check if origination URL exists
#     origination_urls = trunk.origination_urls.list()
#     existing_sip_url = None
    
#     # List existing origination URLs
#     if origination_urls:
#         logging.info("Existing origination URLs:")
#         for url in origination_urls:
#             logging.info(f"  - {url.friendly_name}: {url.sip_url}")
#             if "livekit" in url.friendly_name.lower() or url.sip_url == sip_uri:
#                 existing_sip_url = url
    
#     if existing_sip_url:
#         if existing_sip_url.sip_url != sip_uri:
#             # Update existing origination URL
#             existing_sip_url.update(sip_url=sip_uri)
#             logging.info(f"Updated existing origination URL with new SIP URI: {sip_uri}")
#         else:
#             logging.info("SIP URI already configured correctly")
#     else:
#         # Add new origination URL
#         trunk.origination_urls.create(
#             sip_url=sip_uri,
#             weight=1,
#             priority=1,
#             enabled=True,
#             friendly_name="LiveKit SIP URI",
#         )
#         logging.info(f"Added new origination URL: {sip_uri}")
    
#     return trunk

# def delete_all_trunks_and_create_new(client, sip_uri):
#     """Delete all existing trunks and create a new LiveKit trunk (use with caution)"""
#     existing_trunks = client.trunking.v1.trunks.list()
    
#     # Delete all existing trunks
#     for trunk in existing_trunks:
#         logging.info(f"Deleting trunk: {trunk.sid} ({trunk.friendly_name})")
#         client.trunking.v1.trunks(trunk.sid).delete()
    
#     # Create new trunk
#     domain_name = f"livekit-trunk-{os.urandom(4).hex()}.pstn.twilio.com"
#     trunk = client.trunking.v1.trunks.create(
#         friendly_name="LiveKit Trunk",
#         domain_name=domain_name,
#     )
    
#     # Add origination URL
#     trunk.origination_urls.create(
#         sip_url=sip_uri,
#         weight=1,
#         priority=1,
#         enabled=True,
#         friendly_name="LiveKit SIP URI",
#     )
    
#     logging.info(f"Created new LiveKit Trunk: {trunk.sid}")
#     return trunk

# def create_inbound_trunk(phone_number):
#     trunk_data = {
#         "trunk": {
#             "name": "Inbound LiveKit Trunk",
#             "numbers": [phone_number]
#         }
#     }
#     with open('inbound_trunk.json', 'w') as f:
#         json.dump(trunk_data, f, indent=4)

#     result = subprocess.run(
#         ['lk', 'sip', 'inbound', 'create', 'inbound_trunk.json'],
#         capture_output=True,
#         text=True
#     )

#     if result.returncode != 0:
#         logging.error(f"Error executing command: {result.stderr}")
#         return None

#     match = re.search(r'ST_\w+', result.stdout)
#     if match:
#         inbound_trunk_sid = match.group(0)
#         logging.info(f"Created inbound trunk with SID: {inbound_trunk_sid}")
#         return inbound_trunk_sid
#     else:
#         logging.error("Could not find inbound trunk SID in output.")
#         return None

# def create_dispatch_rule(trunk_sid):
#     dispatch_rule_data = {
#         "name": "Inbound Dispatch Rule",
#         "trunk_ids": [trunk_sid],
#         "rule": {
#             "dispatchRuleIndividual": {
#                 "roomPrefix": "call-"
#             }
#         }
#     }
#     with open('dispatch_rule.json', 'w') as f:
#         json.dump(dispatch_rule_data, f, indent=4)

#     result = subprocess.run(
#         ['lk', 'sip', 'dispatch-rule', 'create', 'dispatch_rule.json'],
#         capture_output=True,
#         text=True
#     )

#     if result.returncode != 0:
#         logging.error(f"Error executing command: {result.stderr}")
#         return

#     logging.info(f"Dispatch rule created: {result.stdout}")

# def main():
#     load_dotenv()
#     logging.basicConfig(level=logging.INFO)

#     account_sid = get_env_var("TWILIO_ACCOUNT_SID")
#     auth_token = get_env_var("TWILIO_AUTH_TOKEN")
#     phone_number = get_env_var("PHONE_NUMBER")
#     sip_uri = get_env_var("LIVEKIT_SIP_URI")

#     client = Client(account_sid, auth_token)

#     # Choose one of the following options:
    
#     # Option 1: Use existing trunk and update if needed (RECOMMENDED)
#     livekit_trunk = get_or_update_livekit_trunk(client, sip_uri)
    
#     # Option 2: Delete all trunks and create new one (CAUTION: This will delete ALL your trunks)
#     # Uncomment the line below and comment out the line above if you want to use this option
#     # livekit_trunk = delete_all_trunks_and_create_new(client, sip_uri)

#     # Continue with inbound trunk creation
#     inbound_trunk_sid = create_inbound_trunk(phone_number)
#     if inbound_trunk_sid:
#         create_dispatch_rule(inbound_trunk_sid)

# if __name__ == "__main__":
#     main()