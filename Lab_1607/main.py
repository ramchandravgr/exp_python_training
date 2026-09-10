import json
import os
import csv

def main():
    print("Hello from lab-1607!")
    input_path = os.path.join(os.path.dirname(__file__), "input.json")
    with open(input_path,"r",encoding="utf-8") as file:
        data = json.load(file)
        realdata = data["results"]
        print(realdata)

    fieldnames = ["consumer_id","name","credit_score","risk_band","delinquent_accounts"]

    output_path = os.path.join(os.path.dirname(__file__), "output.csv")
    with open(output_path,"w",newline="\n",encoding="utf-8") as cfile:
        writer = csv.DictWriter(cfile,fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(realdata)
        print(cfile)
    


if __name__ == "__main__":
    main()
