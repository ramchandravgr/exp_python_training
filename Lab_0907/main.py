def main():
    print("Hello from lab-0907!")
    raw_credit_input = (
    "   \t  Alejandro Moj\u00c3\u00adca  |  555 - 01 - 9999   \t"
    )

    values = raw_credit_input.split("|")

    name = values[0]
    ssn = values[1]
    
    final_name = name.strip().encode("latin-1").decode("utf-8")
    final_ssn = ssn.strip().replace(" ", "")
    
    final_ssn = f"XXX-XX-{final_ssn[-4:]}"

    print(final_name,final_ssn)

if __name__ == "__main__":
    main()
