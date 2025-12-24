"""
Script to import owner names from Second Day Tokan PDF into the database
Transliterates Marathi names to English and inserts them into the owners table
"""
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.models.owner import Owner

# All 200 owner names transliterated from Marathi to English (Token 201-400)
OWNER_NAMES = [
    # Page 1 - Token 201-225
    "Shivaji Bajaba Kanhukar",
    "Vedant Govind Jadhav",
    "Akshay Suresh Kad",
    "Sarthak Kailassheth Tambe",
    "Mangesh Ramdas Thorat",
    "Malganga Mata Bailgada Sanghatna",
    "Kundaliksheth Shankar Sarajite",
    "Pratip Appa Tingre",
    "Matya Group",
    "Sanvi Amol Lokhande",
    "Kai.Patilbuwa Balaji Dabhade",
    "Rakesh Daulat Parhad",
    "Annasaheb Hiraman Marathe",
    "Kishor Genbhau Dangat",
    "Devendra Devaram Devkar",
    "Pavan Nandaram Surve",
    "Gorakshanath Shete",
    "Ramdas Namdev Rale",
    "Ladkya Group Bailgada Sanghatna",
    "Shivaji Khandu Khandve",
    "Ashwinkumar Suryakant Bhandlekar",
    "Pandurang Appa Rambhau Ghare",
    "Pradip Balaso Sahane",
    "Bhaiyya Inamdar",
    "Kai.Pandurang Dattatray Thorat",

    # Page 2 - Token 226-250
    "Adhira Akshay Mungse",
    "Yogesh Machhindresheth Tawahare",
    "Tukaramdada Gyanoba Ambare",
    "Takalkar Patil Bailgada Sanghatna",
    "Dilip Pandarinath Jagtap",
    "Vinayak Sunil Gosavi",
    "Khushal Bhanudas Tapkir",
    "Yogesh Chandrakant Kurhade",
    "Pushkar Rajendra Nevale",
    "Avadhut Rahul Avade",
    "Shrikant Shambu Namjoshi",
    "Rakesh Murlidhar Khandere",
    "Damu Bhimaji Kaduskar",
    "Aishwarya Hrushikesh Desari",
    "Shivraj Kalidaas Munche",
    "Gajaba Maruti Talekar",
    "Vigneshwarda Ganesh Medankar",
    "Ganeshsheth Babanrav Shaut",
    "Praful Kisan Dondkar",
    "Nilesh Nilakanth Mhusade",
    "Aryan Santosh Ingavale",
    "Kishor Kaluram Karde",
    "Akushsheth Shankar Katare",
    "Sunil Mahadev Kadam",
    "Rahul Ghusarav Hade",

    # Page 3 - Token 251-275
    "Manik Dagdu Kharabi",
    "Maruti Pandit Gujar",
    "Rudransh Gorakshanath Wadekar",
    "Arnav Jalindra Pinjan",
    "Vikram Dilip Botre",
    "Swamiraj Omkarsheth Kanhukar",
    "Digambar Haribhau Kadam",
    "Amol Gulabrao Pawar",
    "Laxman Dipak Gulave",
    "Amar Gangaram Murhe",
    "Kunal Dattatray Padval",
    "Genbhau Dagadu Bage",
    "Vijay Raghoji Hundare",
    "Vikidada Diliprao Gade",
    "Nityanshsdada Bantisheth Kalbhore",
    "Sunil Anna Shelke",
    "Sairaj Ravikant Hulavale",
    "Vihan Suresh Dagde",
    "Baban Baburao Ghate",
    "Kai.Hiramansheth Barku Bhagde",
    "Mayurdada Hanumant Ghundare",
    "Kai.Shivaji Baburao Dighe",
    "Baban Kisan Gade",
    "Sai Santosh Kanade",
    "Mahendresheth Bajirao Kaduskar",

    # Page 4 - Token 276-300
    "Kai.Baban Shivram Vandekar",
    "Bhausaheb Dashrath Raut",
    "Abhishek Shivaji Waghmare",
    "Shiv Vikasda Manjare",
    "Rahul Narayan Thigale",
    "Pankajsheth Natha Ghevde",
    "Sambhaji Shripati Shinde",
    "Malhari Pandurang Chavhan",
    "Vedant Sandip Murhe",
    "Atharva Navnath Dondkar",
    "Shivaji Dattoba Birdavde",
    "Balasaheb Sopan Kad",
    "Yashdada Kiran Jadhav",
    "Baban Sadashiv Khedkar",
    "Pranjali Sachin Birdavde",
    "Adhiraj Gyaneshwar Sandbhor",
    "Minde Patil Bailgada Sanghatna",
    "Sudam Ananda Parhad",
    "Swapnil Sandip Deshmukh",
    "Shivash Sandip Chekavde",
    "Martand Bhanudas Alhad",
    "Devram Padanrav Darekar",
    "Vilas Anandrav Kachate",
    "Bhikaji Mhataraba Manke",
    "Chetanbhau Devidas Ghate",

    # Page 5 - Token 301-325
    "Maruti Ranguji Mule",
    "Navnath Sopan Chikhale",
    "Nileshsnana Tukaram Lokhande",
    "Baburao Mahadu Walunj",
    "Kai. Maruti Shankar Kendle",
    "Samarth Mangesh Alhad",
    "Arun Mahadev Raskar",
    "Sagar Piraji Sirsagar",
    "Tejas Bappusaheb Satav",
    "Sandipsheth Anandrao Bhokse",
    "Raya Swapnil Dube",
    "Popat Dagdu Jadhav",
    "Dattasheth Ashok Chate",
    "Tushar Yashwant Davkhar",
    "Chaitanysheth Malhari Pathare",
    "Avinash Balasaheb Karke",
    "Bappu Tukaram Alhad",
    "Mayur Dattatray Dondkar",
    "Ganesh Suresh Pingale",
    "Santosh Madhukar Gavde",
    "Amolsheth Rannath Darekar",
    "Kailas Vishnu Thorat",
    "Vedantaraje Purushottam Narvade",
    "Suniltatya Nivritti Pathare",
    "Jai Hanuman Bailgada Sanghatna",

    # Page 6 - Token 326-350
    "Abhiraj Vishnu Gavari",
    "Pranav Shamrao Shinde",
    "Sahadu Ganpat Topale",
    "Pandurang Kisan Kale",
    "Sagar Subhash Chaudhari",
    "Mangesh Navnath Agarkar",
    "Manoj Subhash More",
    "Pranyatai Rishikesh Mohite",
    "Bhagwan Baburav Gavde",
    "Ganesh Bajishav Garhane",
    "Santosh Kisanrav Potale",
    "Prathmesh Mahadev Baghale",
    "Vikas Bharat Bhandlekar",
    "Babajisheth Vilas Jeur",
    "Dhananjay Kisan Jare",
    "Savleshav Umarji Rokde (Sarpanch)",
    "Laxman Baburav Kale",
    "Jivash Ajit Kaloje",
    "Anup Vishal Pamap",
    "Pintya Group",
    "V.Nathuram Rambhau Dhumal",
    "Nitin Mahadu Tingre",
    "Kartikraje Akshay Bagar",
    "Aditya Rahulsheth Satpute",
    "Adhira Akash Saste",

    # Page 7 - Token 351-375
    "Popat Baban Nehare",
    "Prashant Devidas Lokhande",
    "Digambar Kundalik Sawant",
    "Shivash Medag",
    "Tushararoth Pandurang Mhambare",
    "Yashvardhan Vikas Wadekar",
    "Kanifnath Bailgada Sanghatna",
    "Suryashsdada Ramdas Kunde",
    "Shetannu Sanpatrav Sonvane",
    "Pratik Gulab Minde",
    "Ranjit Hanumant Mohite",
    "Vikassheth Vilasrav Pachundkar",
    "Ghare Patil Bailgada Sanghatna",
    "Amarbandada Anirudha Jadhav",
    "Bhagwan Baburav Shinde",
    "Mei. Yogavir Sandip Sakore",
    "Jivandada Sitaram Korhale",
    "Sachin Kailas Modhve",
    "Parshuram Prabhu Bonhade",
    "Kai. Trambak Ramji Shivale",
    "Viradada Vilas Yelvande",
    "Swapnil Rohidas Navale",
    "Dipsheth Shivram Murhe",
    "Santosh Raghunath Darekar",
    "Mahakaleshwar Bailgada Sanghatna",

    # Page 8 - Token 376-400
    "Motya Shiva Bailgada Sanghatna",
    "Amit Popat Shinde",
    "Kamanesh Dadabhau Ghadge",
    "Kai.Dagdusheth Vithoba Dope",
    "Ganeshsheth Vamnarav Indore",
    "Shivaji Namdev Pokharkar",
    "Babanrav Kisan Raut",
    "Kaivalysdada Kiran Mhambare",
    "Prakasheth Shinde",
    "Bandisheth Gyaneshwar Kamde",
    "Narayan Chitulrav More",
    "Kanifnath Bailgada Sanghatna",
    "Rajavir Dayanand Jagadale",
    "Dattobasheth Arjun Phad",
    "Ranvir Ajit Rakhe",
    "Vishnu Ananta Hole",
    "Pritmesheth Tushar Dhavde",
    "Ramdas Ishvar Padval",
    "Rudra Ganesh Yelvande",
    "Balasaheb Khanduji Gade",
    "Shishal Balasaheb Manjare",
    "Kai.Ananda Bappu Pacharane",
    "Nitin Genbhau Thombare",
    "Baban Narayan Salunkhe",
]


def import_owners():
    """Import owner names into the database"""
    db: Session = SessionLocal()

    try:
        stats = {
            'total': len(OWNER_NAMES),
            'inserted': 0,
            'skipped': 0,
            'errors': 0
        }

        print(f"Starting import of {stats['total']} owners from Second Day Tokan...")
        print("-" * 60)

        for idx, full_name in enumerate(OWNER_NAMES, 1):
            try:
                # Check if owner already exists
                existing_owner = db.query(Owner).filter(
                    Owner.full_name == full_name
                ).first()

                if existing_owner:
                    print(f"[{idx:3d}] SKIPPED: {full_name} (already exists)")
                    stats['skipped'] += 1
                    continue

                # Create new owner
                new_owner = Owner(full_name=full_name)
                db.add(new_owner)
                db.commit()

                print(f"[{idx:3d}] INSERTED: {full_name}")
                stats['inserted'] += 1

            except Exception as e:
                db.rollback()
                print(f"[{idx:3d}] ERROR: {full_name} - {str(e)}")
                stats['errors'] += 1

        print("-" * 60)
        print(f"\nImport Summary:")
        print(f"  Total:    {stats['total']}")
        print(f"  Inserted: {stats['inserted']}")
        print(f"  Skipped:  {stats['skipped']} (duplicates)")
        print(f"  Errors:   {stats['errors']}")

    except Exception as e:
        print(f"Fatal error during import: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    import_owners()