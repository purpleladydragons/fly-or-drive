import sqlite3

con = sqlite3.connect('flyordrive/db.sqlite3')
cur = con.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS airport 
                (id INTEGER NOT NULL PRIMARY KEY, aita_code text, lat text, lng text);""")

with open('flyordrive/major_airport_locations.txt', 'r') as f:
    lines = f.readlines()
    for line in lines:
        code,coords = line.split(';')
        lat,lng = coords.split(',')
        print(f"Inserting {code}")
        cur.execute(f"""INSERT INTO airport (aita_code, lat, lng) 
                        VALUES ('{code}', '{lat}', '{lng}');""")
    con.commit()
