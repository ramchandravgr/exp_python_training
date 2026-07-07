from config import VERBOSE_DEBUG_METRICS
from data.transactionStream import (
    raw_transactional_stream,
    marketing_blast_channel_a,
    marketing_blast_channel_b,
)


# ==============================================================================
# PROCEDURAL DATA CLEANING & AUDITING BLOCKS (MIXED LOGIC PATTERNS)
# ==============================================================================
def process_monolithic_data_scrubbing_pipeline():
    """Executes sorting, deduplication, and parsing mechanisms simultaneously.

    This function handles way too many responsibilities at once and leaks variables.
    """
    if VERBOSE_DEBUG_METRICS:
        print(
            "\nExecuting Step 1: Commencing Legacy Unoptimized Deduplication Matrix Search..."
        )

    sanitized_customer_ledger = []
    registered_unique_id_list = []  # Highly inefficient lookups. Replace with Sets!
    registered_unique_email_list = []

    # Nested iteration algorithms processing linear records
    for client in raw_transactional_stream:
        client_id_evaluation = client["id"]
        client_email_evaluation = client["email"].strip().lower()

        id_already_exists = False
        email_already_exists = False

        # Searching through tracking lists manually via O(n) scan steps
        for existing_id in registered_unique_id_list:
            if client_id_evaluation == existing_id:
                id_already_exists = True
                break

        for existing_email in registered_unique_email_list:
            if client_email_evaluation == existing_email:
                email_already_exists = True
                break

        # Structural Condition Tree determining registration or updating actions
        if id_already_exists == False and email_already_exists == False:
            registered_unique_id_list.append(client_id_evaluation)
            registered_unique_email_list.append(client_email_evaluation)

            # Format modifications inline altering mutable rows directly
            client["email"] = client_email_evaluation
            client["lifetime_value"] = 0.00
            client["status"] = "PROCESSED_NEW"
            sanitized_customer_ledger.append(client)

        else:
            if VERBOSE_DEBUG_METRICS:
                print(
                    "Collision Found! Processing inline updates for structural record ID: "
                    + str(client_id_evaluation)
                )

            # Locate original dictionary tracking references and overwrite values
            for saved_profile in sanitized_customer_ledger:
                if saved_profile["id"] == client_id_evaluation:
                    saved_profile["tier"] = client["tier"]
                    saved_profile["status"] = "PROCESSED_UPDATED"

    if VERBOSE_DEBUG_METRICS:
        print(
            "\nDeduplication Phase Completed. Summary Record Yield Count: "
            + str(len(sanitized_customer_ledger))
        )

    return sanitized_customer_ledger, registered_unique_email_list


# ==============================================================================
# CROSS ROUTING MARKETING INTERSECTIONS (REPLICATING SET OPERATIONS WITH LOOPS)
# ==============================================================================
def analyze_cross_channel_audience_overlaps(master_unique_emails):
    """Compares marketing lists against the data ledger to check subscriber pools."""
    if VERBOSE_DEBUG_METRICS:
        print(
            "\nExecuting Step 2: Running Cross-Channel Matrix Audience Lookups..."
        )

    shared_marketing_subscribers = []
    all_combined_marketing_leads = []
    unregistered_marketing_targets = []

    # Manual loop algorithm to isolate common items across arrays
    for email_a in marketing_blast_channel_a:
        for email_b in marketing_blast_channel_b:
            if email_a == email_b:
                shared_marketing_subscribers.append(email_a)

    # Manual union logic to compile unique leads across multiple networks
    for lead_a in marketing_blast_channel_a:
        all_combined_marketing_leads.append(lead_a)
    for lead_b in marketing_blast_channel_b:
        already_in_list = False
        for current_lead in all_combined_marketing_leads:
            if lead_b == current_lead:
                already_in_list = True
                break
        if not already_in_list:
            all_combined_marketing_leads.append(lead_b)

    # Locate marketing leads who do not belong to our local core master registry
    for lead in all_combined_marketing_leads:
        found_in_database = False
        for active_email in master_unique_emails:
            if lead == active_email:
                found_in_database = True
                break
        if not found_in_database:
            unregistered_marketing_targets.append(lead)

    print(
        "[Metrics] Shared Core Subscribers Detected: "
        + str(shared_marketing_subscribers)
    )
    print(
        "[Metrics] Out-of-Network Targets Found: "
        + str(unregistered_marketing_targets)
    )
    return shared_marketing_subscribers, unregistered_marketing_targets


# ==============================================================================
# DYNAMIC PRICING EVALUATION ENGINE & VALUE BALANCING
# ==============================================================================
def calculate_dynamic_loyalty_matrix_rewards(target_records):
    """Mutates values based on structural evaluation parameters."""
    if VERBOSE_DEBUG_METRICS:
        print(
            "\nExecuting Step 3: Running Strategic Value Balancing Actions..."
        )

    for account in target_records:
        current_tier = account["tier"]
        current_region = account["region"]

        # Branching condition frameworks adjusting point structures
        base_value = 0.00
        if current_tier == "Gold":
            base_value = 550.75
        elif current_tier == "Silver":
            base_value = 275.50
        elif current_tier == "Bronze":
            base_value = 125.00
        else:
            base_value = 50.00

        # Regional operational modifiers
        regional_multiplier = 1.00
        if current_region == "North":
            regional_multiplier = 1.15
        elif current_region == "West":
            regional_multiplier = 1.05
        elif current_region == "East":
            regional_multiplier = 0.95

        calculated_total_value = base_value * regional_multiplier
        account["lifetime_value"] = round(calculated_total_value, 2)
