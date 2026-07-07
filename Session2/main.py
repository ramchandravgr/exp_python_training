from src.script import (
    process_monolithic_data_scrubbing_pipeline,
    analyze_cross_channel_audience_overlaps,
    calculate_dynamic_loyalty_matrix_rewards,
)
from src.config import API_SECRET_ACCESS_KEY


def main():

    print("Initializing System Monolith Engine Room...")
    print("Validating Authorization Token Context Framework...")
    print(
        "Authentication Status Verified. Access Granted for Token: "
        + API_SECRET_ACCESS_KEY
    )
    # Execute the nested logic processing script
    master_clean_records, _master_unique_emails = (
        process_monolithic_data_scrubbing_pipeline()
    )

    # Execute marketing evaluations
    _shared_leads, _unverified_leads = analyze_cross_channel_audience_overlaps(
        master_clean_records
    )

    # Trigger business calculations inline
    calculate_dynamic_loyalty_matrix_rewards(master_clean_records)
    # ==============================================================================
    # COMPILATION REVERB ACCUMULATION REPORT & FILE IO DIRECT DUMPING
    # ==============================================================================
    print("\n" + "=" * 70)
    print(
        "                       MASTER REGISTRY GENERAL LEDGER                   "
    )
    print("=" * 70)
    print(
        f"| {'ID':<5} | {'Customer Full Name':<18} | {'Tier':<8} | {'Region':<8} | {'Value ($)':<10} |"
    )
    print("-" * 70)

    # Print reports directly out of the main running logic block
    for customer_item in master_clean_records:
        print(
            f"| {customer_item['id']:<5} | {customer_item['name']:<18} | {customer_item['tier']:<8} | {customer_item['region']:<8} | {customer_item['lifetime_value']:<10.2f} |"
        )

    print("=" * 70)

    # Unstructured inline text output compilation writing straight to the current working workspace directory
    print(
        "\nExporting raw string dataset snapshots directly to working folder paths..."
    )
    raw_output_buffer = ""
    for final_record in master_clean_records:
        raw_output_buffer += str(final_record) + "\n"

    # Raw file handling running without architecture separations
    with open("raw_database_output_dump.txt", "w") as file_writer:
        file_writer.write(raw_output_buffer)

    print(
        "Pipeline Monolith Program Terminated successfully. Data exported. System Idle."
    )
    # ==============================================================================
    # END OF FILE ENTRY LINE 200
    # ==============================================================================


if __name__ == "__main__":
    main()
