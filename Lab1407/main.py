import re

def main():
    print("Hello from lab1407!")
    input = "log_entry_09: proc_error %$! item: PRD-9981 priced at $45.99 ... user_id_none.. 2023-11-01 end_log."
    product_code_pattern = r"PRD\-\d{4}"
    price_pattern = r"\$\d+\.\d+"
    date_pattern = r"\d{4}\-\d{2}\-\d{2}"

    pcp_match = re.search(product_code_pattern,input)
    pp_match = re.search(price_pattern, input)
    dp_match = re.search(date_pattern,input)

    final_output = {}
    final_output["product_code"] = pcp_match.group()
    final_output["price"] = pp_match.group()
    final_output["date"] = dp_match.group()


    print(final_output)


if __name__ == "__main__":
    main()
