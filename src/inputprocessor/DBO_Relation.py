from src.db.SqlConnector import SqlConnConcepts
from src.inputprocessor.Relation import Relation

def get_all_relations_templates():
    sql = "SELECT idrelations, " \
          "relation," \
          "first," \
          "keywords," \
          "second " \
          "FROM relations_templates "

    conn = SqlConnConcepts.get_connection()
    cursor = conn.cursor()

    resulting = []

    try:
        cursor.execute(sql)
        result = cursor.fetchall()

        for row in result:
            id          = row[0]
            relation    = row[1]
            first       = row[2]
            keywords    = row[3]
            second      = row[4]

            resulting.append(Relation(id, relation, first, keywords, second))

    except:
        print("Error Relations Templates: unable to fetch all data")

    conn.close()
    return resulting

def get_matching_relation_pattern(first, keywords, second):
    sql = "SELECT idrelations, " \
          "relation " \
          "FROM relations_templates" \
          "WHERE first = %s AND second = %s AND keywords = %s "

    conn = SqlConnConcepts.get_connection()
    cursor = conn.cursor()

    resulting = None

    try:
        # Execute the SQL command
        cursor.execute(sql, (first, second, keywords,))
        # Fetch all the rows in a list of lists.
        result = cursor.fetchone()

        if result != None:
            id          = result[0]
            relation    = result[1]

            resulting = (Relation(id, relation, first, keywords, second))

    except:
        print("Error Relation: unable to fetch data for word "+first+" and "+second)

    conn.close()
    return resulting