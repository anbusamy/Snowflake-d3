import snowflake.connector
import json

# Snowflake connection details
conn = snowflake.connector.connect(
    user='USER_ALEX',
    password='1235123!3463443',
    account='apssword',
    warehouse='compute_wh',
    role='ACCOUNTADMIN',
    database='SNOWFLAKE',
    schema='ACCOUNT_USAGE'
)

def rows_to_dict_list(cursor, rows):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in rows]

# Fetch data from Snowflake
def fetch_data(query):
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result



userss=fetch_data("SELECT name FROM USERS;")
users = [row[0] for row in userss]

roless=fetch_data("SELECT name FROM ROLES;")
roles = [row[0] for row in roless]

grants_to_users = fetch_data("SELECT grantee_name AS user, role FROM GRANTS_TO_USERS;")
user_roles = grants_to_users

rolepr = fetch_data("""
    SELECT DISTINCT GRANTEE_NAME AS role, privilege, granted_on AS object_type, 
                    table_catalog, grant_option 
    FROM GRANTS_TO_ROLES 
    WHERE granted_to = 'ROLE' AND granted_on IN ('SCHEMA','TABLE','DATABASE');
""")
role_privileges = rolepr


# Step 3: Build the tree structure
tree = {"name": "Snowflake Access Tree", "children": []}

# Organize roles and privileges for quick lookup
role_priv_map = {}
for role, privilege, object_type, catalog, grant_option in role_privileges:
    if role not in role_priv_map:
        role_priv_map[role] = []
    role_priv_map[role].append({
        "name": f"{object_type}: {catalog} [{privilege}]",
        "grant_option": grant_option
    })


# Organize user-role mapping
user_map = {}
for user, role in user_roles:
    if user not in user_map:
        user_map[user] = []
    user_map[user].append(role)

# Build JSON
for user in sorted(user_map):
    user_node = {"name": user, "children": []}
    for role in user_map[user]:
        role_node = {"name": role, "children": []}
        for priv in role_priv_map.get(role, []):
            role_node["children"].append({
                "name": priv["name"] + (" [GRANTABLE]" if priv["grant_option"] == "YES" else "")
            })
        user_node["children"].append(role_node)
    tree["children"].append(user_node)

# Step 4: Output to JSON file
with open("snowflake_d3_tree.json", "w") as f:
    json.dump(tree, f, indent=4)

print("D3-compatible JSON saved to 'snowflake_d3_tree.json'")
