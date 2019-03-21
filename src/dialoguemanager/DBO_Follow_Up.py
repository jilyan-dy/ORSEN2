from src.db.SqlConnector import SqlConnConcepts
from .Follow_Up import Follow_Up

def get_specific_follow_up_template(id):
    sql = "SELECT idfollow_up, " \
          "template_id, " \
          "follow_up_template, " \
          "concept_letter " \
          "FROM follow_up_templates " \
          "WHERE template_id = %d;" % id

    conn = SqlConnConcepts.get_connection()
    cursor = conn.cursor()

    resulting = None

    try:
        # Execute the SQL command
        cursor.execute(sql)
        # Fetch all the rows in a list of lists.
        result = cursor.fetchone()
        row = result
        id                    = row[0]
        template_id           = row[1]
        follow_up_template    = row[2]
        concept_letter        = row[3]

        follow_up_template = follow_up_template.split("|")

        resulting = Follow_Up(id, template_id , follow_up_template, concept_letter)
    except:
        print("Error FOLLOW UP TEMPLATES: unable to fetch follow up template #%d" % id)

    conn.close()
    return resulting