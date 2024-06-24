import mysql.connector
import json
import re
import csv
import os

def connect_to_database():
    return mysql.connector.connect(
        host="localhost",
        user="ritesh",
        password="12345",
        database="pen_collection"
    )

def is_valid_date(date_str):
    # Validate date format (YYYY-MM-DD)
    return re.match(r'\d{4}-\d{2}-\d{2}', date_str) is not None


def is_valid_price(price_str):
    # Validate price format (numeric)
    try:
        price = float(price_str)
        return price >= 0
    except ValueError:
        return False
def export_to_csv(cursor):
    cursor.execute("SELECT * FROM pens")
    pens = cursor.fetchall()

    with open('penCollection.csv', 'w', newline='') as csvfile:
        fieldnames = ['ID', 'Brand', 'Model', 'Color', 'Nib Size', 'Ink Color', 'Purchase Date', 'Price', 'Notes']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for pen in pens:
            writer.writerow({
                'ID': pen[0],
                'Brand': pen[1],
                'Model': pen[2],
                'Color': pen[3],
                'Nib Size': pen[4],
                'Ink Color': pen[5],
                'Purchase Date': pen[6].strftime('%Y-%m-%d'),
                'Price': float(pen[7]),
                'Notes': pen[8]
            })

def reset_ids(cursor, cnx):
    cursor.execute("SELECT * FROM pens ORDER BY id")
    pens = cursor.fetchall()
    
    new_id = 1
    for pen in pens:
        cursor.execute("UPDATE pens SET id = %s WHERE id = %s", (new_id, pen[0]))
        new_id += 1
    cnx.commit()


def add_pen(cursor,cnx):
    brand = input("Enter pen brand: ")
    model = input("Enter pen model: ")
    # Check for redundancy
    cursor.execute("SELECT * FROM pens WHERE brand = %s AND model = %s", (brand, model))
    pen = cursor.fetchone()

    if pen:
        print(f"Pen with brand '{brand}' and model '{model}' already exists.")
        increment_choice = input("Do you want to increment the quantity by 1? (yes/no): ").strip().lower()
        if increment_choice == 'yes':
            new_quantity = pen[9] + 1
            cursor.execute("UPDATE pens SET quantity = %s WHERE id = %s", (new_quantity, pen[0]))
            cnx.commit()
            print("Quantity incremented successfully!")
            return
        else:
            new_record_choice = input("Do you want to add a new record with this brand and model? (yes/no): ").strip().lower()
            if new_record_choice != 'yes':
                print("Operation cancelled.")
                return
    # Get the last entry's id
    cursor.execute("SELECT MAX(id) FROM pens")
    last_id = cursor.fetchone()[0]
    new_id = last_id + 1 if last_id is not None else 1

    # Prompt remaining inputs for new entry
    
    color = input("Enter pen color: ")
    nib_size = input("Enter nib size: ")
    ink_color = input("Enter ink color: ")
    purchase_date = input("Enter purchase date (YYYY-MM-DD): ")
    while not is_valid_date(purchase_date):
        print("Invalid date format. Please enter date in YYYY-MM-DD format.")
        purchase_date = input("Enter purchase date (YYYY-MM-DD): ")

    price = float(input("Enter price: "))
    while not is_valid_price(price):
        print("Invalid price. Please enter a non-negative number.")
        price = input("Enter price: ")

    notes = input("Enter notes: ")

    quantity = int(input("Enter the quantity of the pen: "))

    add_pen_query = ("INSERT INTO pens "
                     "(id,brand, model, color, nib_size, ink_color, purchase_date, price, notes, quantity) "
                     "VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s, %s)")
    pen_data = (new_id,brand, model, color, nib_size, ink_color, purchase_date, price, notes, quantity)
    try:
        cursor.execute(add_pen_query, pen_data)
        cnx.commit()
        print("Pen added successfully!")
    except mysql.connector.Error as err:
        print("Error:", err)
    
    # Export to CSV after adding the pen
    export_to_csv(cursor)

def list_pens(cursor, order_by=None, order=None):
    query = "SELECT * FROM pens"
    if order_by and order:
        query += f" ORDER BY {order_by} {order}"
    cursor.execute(query)
    pens = cursor.fetchall()
    pens_list = []
    for pen in pens:
        pens_list.append({
            "ID": pen[0],
            "Brand": pen[1],
            "Model": pen[2],
            "Color": pen[3],
            "Nib Size": pen[4],
            "Ink Color": pen[5],
            "Purchase Date": pen[6].strftime('%Y-%m-%d'),
            "Price": float(pen[7]),
            "Notes": pen[8]
        })
    print(json.dumps(pens_list, indent=4))

def search_pens(cursor, keyword=None, brand=None, model=None):
    query = "SELECT * FROM pens WHERE"
    conditions = []
    params = []

    if keyword:
        conditions.append("notes LIKE %s")
        params.append(f"%{keyword}%")
    if brand:
        conditions.append("brand = %s")
        params.append(brand)
    if model:
        conditions.append("model = %s")
        params.append(model)

    if not conditions:
        print("No search criteria provided.")
        return

    query += " AND ".join(conditions)
    cursor.execute(query, params)
    pens = cursor.fetchall()
    
    if pens:
        print("\nPens matching the criteria:")
        pens_list = []
        for pen in pens:
            pens_list.append({
                "ID": pen[0],
                "Brand": pen[1],
                "Model": pen[2],
                "Color": pen[3],
                "Nib Size": pen[4],
                "Ink Color": pen[5],
                "Purchase Date": pen[6].strftime('%Y-%m-%d'),
                "Price": float(pen[7]),
                "Notes": pen[8]
            })
        print(json.dumps(pens_list, indent=4))
    else:
        print("\nNo pens found matching the keyword.")



def update_pen(cursor,cnx):
    pen_id = input("Enter the id of the pen you want to update: ")

    # Check if the pen with the specified id exists
    cursor.execute("SELECT * FROM pens WHERE `id` = %s", (pen_id,))
    pen = cursor.fetchone()
    if not pen:
        print("Pen with id {} does not exist.".format(pen_id))
        return

    print("\nCurrent details of the pen:")
    print("Brand: ", pen[1])
    print("Model: ", pen[2])
    print("Color: ", pen[3])
    print("Nib Size: ", pen[4])
    print("Ink Color: ", pen[5])
    print("Purchase Date: ", pen[6].strftime('%Y-%m-%d'))
    print("Price: ", float(pen[7]))
    print("Notes: ", pen[8])
    print("Quantity: ", pen[9])

    # Prompt the user to choose which attribute(s) to update
    update_choice = input("\nEnter the number(s) of the attribute(s) you want to update "
                          "(1: Brand, 2: Model, 3: Color, 4: Nib Size, 5: Ink Color, "
                          "6: Purchase Date, 7: Price, 8: Notes, 9: Quantity, separated by commas): ")
    update_choice_list = [int(x.strip()) for x in update_choice.split(",")]

    # Prompt the user to enter the new value(s) for the selected attribute(s)
    for choice in update_choice_list:
        if choice == 1:
            new_brand = input("\nEnter new brand: ")
            cursor.execute("UPDATE pens SET brand = %s WHERE `id` = %s", (new_brand, pen_id))
        elif choice == 2:
            new_model = input("\nEnter new model: ")
            cursor.execute("UPDATE pens SET model = %s WHERE `id` = %s", (new_model, pen_id))
        elif choice == 3:
            new_color = input("\nEnter new color: ")
            cursor.execute("UPDATE pens SET color = %s WHERE `id` = %s", (new_color, pen_id))
        elif choice == 4:
            new_nib_size = input("\nEnter new nib size: ")
            cursor.execute("UPDATE pens SET nib_size = %s WHERE `id` = %s", (new_nib_size, pen_id))
        elif choice == 5:
            new_ink_color = input("\nEnter new ink color: ")
            cursor.execute("UPDATE pens SET ink_color = %s WHERE `id` = %s", (new_ink_color, pen_id))
        elif choice == 6:
            new_purchase_date = input("\nEnter new purchase date (YYYY-MM-DD): ")
            while not is_valid_date(new_purchase_date):
                print("Invalid date format. Please enter date in YYYY-MM-DD format.")
                new_purchase_date = input("\nEnter new purchase date (YYYY-MM-DD): ")
            
            cursor.execute("UPDATE pens SET purchase_date = %s WHERE `id` = %s", (new_purchase_date, pen_id))
        elif choice == 7:
            new_price = float(input("\nEnter new price: "))
            while not is_valid_price(new_price):
                print("Invalid price. Please enter a non-negative number.")
                new_price = input("\nEnter new price: ")
            
            cursor.execute("UPDATE pens SET price = %s WHERE `id` = %s", (new_price, pen_id))
        elif choice == 8:
            new_notes = input("\nEnter new notes: ")
            cursor.execute("UPDATE pens SET notes = %s WHERE `id` = %s", (new_notes, pen_id))

        elif choice == 9:
            new_quantity = int(input("\nEnter new Quantity: "))
            cursor.execute("UPDATE pens SET quantity = %d WHERE 'id' = %s", (new_quantity, pen_id))

    cnx.commit()
    print("Pen updated successfully!")

    # Export to CSV after updating the pen
    export_to_csv(cursor)

def delete_pen(cursor):
    pen_id = input("Enter the ID of the pen you want to delete: ")

    cursor.execute("SELECT * FROM pens WHERE id = %s", (pen_id,))
    pen = cursor.fetchone()
    if not pen:
        print("Pen with ID {} does not exist.".format(pen_id))
        return

    confirmation = input("Are you sure you want to delete this pen? (yes/no): ")
    if confirmation.lower() == "yes":
        cursor.execute("DELETE FROM pens WHERE id = %s", (pen_id,))
        print("Pen deleted successfully!")
    else:
        print("Deletion canceled.")

    # Export to CSV after deleting the pen
    export_to_csv(cursor)


def additional_features_menu(cursor,cnx):
    print("\nAdditional Features:")
    print("1. Total price of all pens")
    print("2. Show quantity of pens with respect to brand")
    print("3. Counting Options")
    print("4. Reset IDs to be uniform")
    print("5. Get Exact location of CSV File (stored in pc)")
    print("6. Back to main menu")

    choice = input("Enter your choice (1-4): ").strip()

    if choice == '1':
        total_price_of_pens(cursor)
    elif choice == '2':
        show_pens_with_quantity(cursor)
    elif choice == '3':
        print("\nCounting Options:")
        print("1. Total number of pens I possess (including redundant pens)")
        print("2. Total number of pens I possess (excluding redundant pens)")
        print("3. Number of pens of a specific brand or model")
        print("4. Number of pens more expensive than a certain price")
        print("5. Number of pens of a certain color")
        count_choice = input("Enter your counting choice (1-5): ")

        if count_choice == '1':
            total_number_of_pens(cursor, include_redundant=True)
        elif count_choice == '2':
            total_number_of_pens(cursor, include_redundant=False)
        elif count_choice == '3':
            attribute = input("Enter brand or model name: ")
            pens_of_brand_or_model(cursor, attribute)
        elif count_choice == '4':
            price = float(input("Enter price threshold: "))
            pens_more_expensive_than(cursor, price)
        elif count_choice == '5':
            color = input("Enter color: ")
            pens_of_color(cursor, color)
    elif choice == '4':
            reset_ids(cursor, cnx)
            print("IDs have been reset to be uniform.")            

    elif choice == '5':
        filename = 'penCollection.csv'
        # Get the absolute path of the CSV file
        csv_path = os.path.abspath(filename)
        print(f"The CSV file has been created at: {csv_path}")


    elif choice == '6':
        pass  # Simply return to the main menu
    else:
        print("Invalid choice. Please enter a number between 1 and 4.")

def total_price_of_pens(cursor):
    cursor.execute("SELECT SUM(price) FROM pens")
    total_sum = cursor.fetchone()[0]
    print(f"\nTotal price of all pens: INR {total_sum:.2f}")

def show_pens_with_quantity(cursor):
    cursor.execute("SELECT brand, COUNT(*) AS quantity FROM pens GROUP BY brand")
    pens = cursor.fetchall()

    print("\nQuantity of pens with respect to brand:")
    for pen in pens:
        print(f"{pen[0]} - Quantity: {pen[1]}")

#Manipulations WRT quantity column
def total_number_of_pens(cursor, include_redundant=True):
    if include_redundant:
        cursor.execute("SELECT SUM(quantity) FROM pens")
    else:
        cursor.execute("SELECT COUNT(DISTINCT model) FROM pens")
    total_pens = cursor.fetchone()[0]
    print(f"Total number of pens: {total_pens}")

def pens_of_brand_or_model(cursor, attribute):
    cursor.execute("SELECT SUM(quantity) FROM pens WHERE brand = %s OR model = %s", (attribute, attribute))
    pens_count = cursor.fetchone()[0]
    print(f"Number of pens of brand/model '{attribute}': {pens_count}")

def pens_more_expensive_than(cursor, price):
    cursor.execute("SELECT SUM(quantity) FROM pens WHERE price > %s", (price,))
    pens_count = cursor.fetchone()[0]
    print(f"Number of pens more expensive than ${price}: {pens_count}")

def pens_of_color(cursor, color):
    cursor.execute("SELECT SUM(quantity) FROM pens WHERE color = %s", (color,))
    pens_count = cursor.fetchone()[0]
    print(f"Number of pens of color '{color}': {pens_count}")

#Main implementation

def main():
    cnx = connect_to_database()
    cursor = cnx.cursor()

    while True:
        print("\nPen Collection Menu:")
        print("1. Add a new pen")
        print("2. List all pens")
        print("3. Sort and list pens")
        print("4. Search Pen from Record")
        print("5. Update the pen records")
        print("6. Deletion of pen records")
        print("7. Additional Features")
        print("8. Help")
        print("9. Exit\n")

        choice = input("Enter your choice (1-9): ")

        if choice == '1':
            add_pen(cursor,cnx)
        elif choice == '2':
            list_pens(cursor)
        elif choice == '3':
            print("\nSort Options:")
            print("1. Sort by price (ascending)")
            print("2. Sort by price (descending)")
            print("3. Sort by brand name (ascending)")
            print("4. Sort by brand name (descending)")
            print("5. Sort by model name (ascending)")
            print("6. Sort by model name (descending)")
            sort_choice = input("Enter your sort choice (1-6): ")

            if sort_choice == '1':
                list_pens(cursor, order_by="price", order="ASC")
            elif sort_choice == '2':
                list_pens(cursor, order_by="price", order="DESC")
            elif sort_choice == '3':
                list_pens(cursor, order_by="brand", order="ASC")
            elif sort_choice == '4':
                list_pens(cursor, order_by="brand", order="DESC")
            elif sort_choice == '5':
                list_pens(cursor, order_by="model", order="ASC")
            elif sort_choice == '6':
                list_pens(cursor, order_by="model", order="DESC")
            else:
                print("Invalid sort choice. Please enter a number between 1 and 6.")

        elif choice == '4':
            print("\n\nSearch Options:")
            print("1. Search pens by keyword in notes")
            print("2. Search pens by brand")
            print("3. Search pens by model")
            print("4. Search pens by entering both brand and model")

            search_choice= input("Enter your search choice (1-4): ")
            if search_choice == '1':
                keyword = input("Enter keyword to search in pen notes: ")
                search_by_keyword(cursor, keyword)

            elif search_choice=='2':
                s_brand = input("Enter Brand name to search :")
                search_by_brand(cursor, s_brand)

            elif search_choice=='3':
                s_model = input("Enter Model name to search :")
                search_by_model(cursor, s_model)

            elif search_choice=='4':
                s_brand = input("Enter Brand name to search :")
                s_model = input("Enter Model name to search :")
                search_by_brand_and_model(cursor, s_brand, s_model)

        elif choice == '5':
            update_pen(cursor,cnx)
        elif choice == '6':
            delete_pen(cursor)

        elif choice == '7':
            additional_features_menu(cursor,cnx)

        elif choice == '8':
            print("Welcome to the Pen Collecton Database Access code.\nThis is a user friendly code, through which we can access the records. You can search for any alphanumeric keyword that is stored in the notes column of the table\n\nSOME IMPORTANT TIPS:\n(i) Color will always be in small case \n(ii) Brand and Model name matches exactly as in box/packaging wrt case \n(iii) Separate brand instructions will be written in help section \n(iv) PEN LOCATION LEGEND : \n* ID 10 to 27 inside Yipee noodles plastic container \n* ID 28 to 50 inside BIG transparent container-I \n* ID 51 to 66 ; 107 to 111 ;157,167,171,172 inside Complan box \n* ID 68 to 106 inside BIG transparent container-II \n* ID 148 to 156,158 to 166; 169,170;173 to 178 inside Horlicks container \n* ID 204 to 257 in Cardboard Box Label: PEN BOX \n*ID 142;")
        elif choice == '9':
            print("Exiting program...")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 9.")

    cursor.close()
    cnx.close()

if __name__ == "__main__":
    main()
