"""
Script to import owner names from Tokan 25 PDF into the database
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

# All 200 owner names transliterated from Marathi to English
OWNER_NAMES = [
    "Sanskar Rajendra Kad",
    "Prasadsheth Sanjay Nanekar",
    "Tukaram Bhikuji Gavhane",
    "Sairaj Navnath Barane",
    "Shripati Bhimaji Kaduskar",
    "Kai.Krushnabappu Tambe Patil",
    "Yash Santosh Bhau Gavhane",
    "Dattatray Balasaheb Lande",
    "Mahesh Anna Garud",
    "Jijabhau Bhausaheb Shinde",
    "Narayansheth Nabaji Jare",
    "Vallabhsheth Akshay Murkute",
    "Pailataai Vikas Wadekar",
    "Shauryadada Eknath Kothawale",
    "Durgesh Khanduji Kashid",
    "Nandusheth Anandrao Varpe",
    "Dadasaheb Subhash Walhekar",
    "Govindsheth Gyaneshwar Khillari",
    "Bhausaheb Hanumant Pokharkar",
    "Swapnil Pandurang Bhondve",
    "Akash Namdev Pokharkar",
    "Aryan Ashok Topale",
    "Shivraj Dagdu Chavhan",
    "Suraj Bhaiyya Rajendra Jagadale",
    "Shubham Bhausaheb Hillal",
    "Santosh Bhausaheb Kand",
    "Sohamsheth Sudam Bhau Shevkari",
    "Vaishnavi Ganesh Kale",
    "Rajaram Shankar Shete",
    "Vedant Manoj More",
    "Gyaneshwar Rambhau Wagh",
    "Ramesh Chandrakant Temgire",
    "Ravindra Appasaheb Begde",
    "Ankush Vithoba Nikam",
    "Sahadu Dasrath Pingale",
    "Bapusaheb Vithoba Limble",
    "Sayaji Baburao Kolekar",
    "Rahuldada Gulabrao Jadhav",
    "Chandra Bhan Kisan Pawar",
    "Sudhirsheth Sayaji Khandebharad",
    "H.Bh.P.Mahadev Tukaram Bhambre",
    "Mahendresheth Pandurang Shinde",
    "Yogeshsheth Pandit Gavli",
    "Shivram Dhondiba Amble",
    "Kai.Ramsheth Baburao Thorat",
    "Bandhuprem Bailgada Sanghatna",
    "Shivraj Yashwant Mhesade",
    "Vishalsheth Ramdas Salunkhe",
    "Sandeep Sheth Gangadhar Yadav",
    "Ku.Kalyani Laxman Kute",
    "Yasharaj Kisan Pachange",
    "Vilascheth Babarao Kalokhe",
    "Vihulsheth Balasaheb Dhamale",
    "Pankaj Hanumant Burde",
    "Jalindersheth Rajaram Takalkar",
    "Sanisheth Shantaram Ghadge",
    "Prakashcheth Sharad Kabadi",
    "Balasaheb Bhikaji Wagh",
    "Sarvesh Suraj Bhalerav",
    "Shete Sabhapati Sanghatna",
    "Devansh Prakash Avte",
    "Dyanand Harishchandra Dome",
    "Tukaram Laxman Jadhav",
    "Vyas Chetan Gavde",
    "Mohan Shivram Kale",
    "Anilsheth Bajrang Landge",
    "Bibhishandada Tukaram Bhosle",
    "Sunilsheth Dabhade",
    "Swapnil Sudam Malekar",
    "Siddheshwari Samir Rakhe",
    "Dattatray Anandrao Pachundkar",
    "Bhausaheb Sopan Sutar",
    "Bhanudas Sambhaji Manjare",
    "Shivraj Bapusaheb Dondkar",
    "Vishalsheth Pandurang Dighe",
    "Govind Anil Ganjave",
    "Ramdas Baburao Sandbhor",
    "Kailas Sadashiv Bavle",
    "Gopalksheth Laxman Shingade",
    "Maheshdada Kisanrao Landge",
    "Dinesh Kisanrao Landge",
    "Vasant Sambhaji Gaikwad",
    "Om Ganeshanna Aargade",
    "Santoshbhau Ankush Gavhane",
    "Pappysheth Tukaram Thorave",
    "Santoshcheth Bhaskarrao Chaudhari",
    "Kiran Suresh Ghate",
    "Rutik Gulabrao Nikhade",
    "Namdev Baburao Borhade",
    "Shivansdada Vaibhav Ghumatkar",
    "Sharad Anand Butte",
    "Vishnu Ananda Yelavande",
    "Ganesh Bajirao Gavhane",
    "Arjun Nivritti Satav",
    "Sanjay Jagannath Pawar",
    "Yuvraj Gyanoba Shelar",
    "Diliprao Dattatray Valse",
    "Sagar Appa Dandavate",
    "Amolsheth Dattatray Bahirat",
    "Somnathdata Balasaheb Nanekar",
    "Govind Anil Gajave",
    "Ramdas Baburao Sadbhor",
    "Kailas Sadashiv Bavle",
    "Gopalksheth Laxman Shingade",
    "Maheshdada Kisanrao Landge",
    "Dinesh Kisanrao Landge",
    "Vasant Sambhaji Gaykwad",
    "Om Ganeshanna Aargade",
    "Santoshbhau Ankush Gavhane",
    "Pappusheth Tukaram Thorve",
    "Santosheth Bhaskarrao Chaudhari",
    "Kiran Suresh Ghate",
    "Rutik Gulabrao Nikhade",
    "Namdev Baburao Borhade",
    "Shivashdada Vaibhav Ghumatkar",
    "Sharad Anand Butte",
    "Vishnu Ananda Yelavande",
    "Ganesh Bajirao Gavhane",
    "Arjun Nivritti Satav",
    "Sanjay Jagannath Pawar",
    "Yuvraj Gyanoba Shelar",
    "Diliprao Dattatray Valse",
    "Sagar Appa Dandavate",
    "Amolsheth Dattatray Bahirat",
    "Somnathdata Balasaheb Nanekar",
    "Dattguru Pratishthan",
    "Dinesh Ramdas Phuge",
    "H.Bh.P.Anand Yashwant Varpe",
    "Ganesh Gulab Saste",
    "Hindavi Sagar Pansare",
    "Jai Sachinbhaiyya Landge",
    "Mayankdada Anniket Tavhare",
    "Pruthvi Kartikbhaiyya Landge",
    "Anniket Tanhaji Gade",
    "Dhananjay Dadabhau Lande",
    "Jayganesh Bailgada Sanghatna",
    "Narayan Gulab Avhale Sabhapati",
    "Bhanudas Devram Kate",
    "Mayur Sahebrao Mohite",
    "Tusharsheth Suryakant Mutke",
    "Sukhdevatatya Balasaheb Avde",
    "Ganesh Arjun Satav",
    "Kalusham Narayan Ghende",
    "Mandhekar Bailgada Sanghatna",
    "Shivraj Babasaheb Tapakir",
    "Shavsaheb Balasaheb Nanekar",
    "Vihan Sudarshan Pachpute",
    "Bhimrao Namdev Chavhan",
    "Gyaneshwar Satyaram Chavhan",
    "Sudhir Sahebrao Gadge",
    "Nilesh Gulab Walunj",
    "Vedanna Sambhajiraje Raut",
    "Sopan Malharrao Kad",
    "Prachitai Samadhan Kothawale",
    "Pai.Yash Dattatray Manjare",
    "Dilip Vishnu Watekar",
    "Vishnu Baburao Saste",
    "Pratik Tanaji Potale",
    "Shivatej Morya Kalaje",
    "Sarves Tanhaji Lande",
    "Popat Bajawa Medage",
    "Yash Vilas Shivale",
    "Abhijit Chendiram Gaykwad",
    "Pai.Keshavsheth Shrikrushna Dheranje",
    "Dattasheth Dasrath Takalkar",
    "Yogesh Maharaj Govind Barave",
    "Shambhuraje Vijay Thite",
    "Shivanya Ravindra Bhujbal",
    "Aditya Hanumant Ghundare",
    "Sw.Akshay Bhau Kolekar Bailgada Sanghatna",
    "Mahesh Kailasrao Shinde",
    "Rajendra Pandu Varun Khosle",
    "Bhisha Sunil Pavale",
    "Bapusaheb Kodobha Sakore",
    "Malhar Ketansheth Gaykwad",
    "Swaraj Pradip Shivale",
    "Manik Anand Sandbhor",
    "Vijay Maruti Jadhav",
    "Vinod Ramesh Shinde",
    "Dadabhau Tabaji Ghadge",
    "Kai.Malhari Maruti Kothawale",
    "Shambhuraje Amol Avte",
    "Mahesh Dipak Modak",
    "Sanidada Suresh Gaykwad",
    "Samarth Bailgada Sanghatna",
    "Sw.Amdar Digambar Baloba Begde Bailgada Sanghatna",
    "Bhausaheb Kisan Dondkar",
    "Shrinath Samir Pachpute",
    "Angadsheth Ganesh Gavde",
    "Swapnil Balasaheb Jadhav",
    "Ramnath Vishnu Waringe",
    "Navnath Ramdas Shete",
    "Ashwinitai Ram Chaugule",
    "Bharat Ankush Shinde",
    "Vishalsheth Jalindra Wable",
    "Avinash Sadashiv Landge",
    "Abasaheb Vittal Pansare",
    "Jagannath Baban Talekar",
    "Bajirao Ganpat Shinde",
    "Ranajit Jagannath Gavari",
    "Swaraj Pradip Shivale",
    "Manik Anand Sadbhore",
    "Vijay Maruti Jadhav",
    "Vinod Ramesh Shinde",
    "Dadabhau Tabaji Ghadge",
    "Kai.Malhari Maruti Kothawale",
    "Shambhuraje Amol Avte",
    "Mahesh Dipak Modak",
    "Sanidada Suresh Gaykwad",
    "Samarth Bailgada Sanghatna",
    "Sw.Aamdar Digambar Baloba Begde Bailgada Sanghatna",
    "Bhausaheb Kisan Dondkar",
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

        print(f"Starting import of {stats['total']} owners...")
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
