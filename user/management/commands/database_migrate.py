import psycopg2

old_database = psycopg2.connect(
    database="chowchow_db",
    user="postgres",
    password="",
    host="localhost",
    port="5432"
)

new_database = psycopg2.connect(
    database="lims",
    user="postgres",
    password="",
    host="localhost",
    port="5432"
)

count = 0



def create_food_customization(junction_table,current_user, vendor_id, food_item_id):
    old_vendor_category = old_database.cursor()
    for each_id in junction_table:
        old_vendor_category.execute(f'''
                                select categories_id from menu_foodaddonsfoodjunction where id = {each_id[0]}
                                '''
                                )
        addon_id = old_vendor_category.fetchone()

        addon = old_database.cursor()
        addon.execute(f"select * from menu_foodaddons where id = {addon_id[0]}")
        addon_detail = addon.fetchall()

        
        column_names = [desc[0] for desc in addon.description]
        result = [dict(zip(column_names, row)) for row in addon_detail]

        old_result = result[0]

        new_user_profile = new_database.cursor()

        new_user_profile.execute(f"""
                                select id from menu_customizationtitle where add_on_category = '{old_result['add_on_category']}'
                                """)
        new_id = new_user_profile.fetchone()

        if not new_id:
            new_user_profile.execute("""
                                    Insert into menu_customizationtitle (minimum_quantity,maximum_quantity,
                                    add_on_category,select_type,description,created_by_id
                                    ) 
                                    values(%s,%s,%s,%s,%s,%s)
                                    RETURNING id;

                                    """,
                                    (old_result['minimum_requirements'],old_result['maximum_order'],
                                    old_result['add_on_category'],old_result['select_type'],old_result['add_on_category'],vendor_id)
                                    
                                    )
            new_id = new_user_profile.fetchone()[0]
            new_database.commit()
        else:
            new_id = new_id[0]

        addons_food_items = old_database.cursor()
        addons_food_items.execute(f"""
                                    select * from menu_addons where food_addons_id = {each_id[0]}
                                    """)
        adons_details = addons_food_items.fetchall()

        column_names = [desc[0] for desc in addons_food_items.description]
        result = [dict(zip(column_names, row)) for row in adons_details]
        many_results = result

        for each_result in many_results:
            new_addons = new_database.cursor()

            multiple_selection =True if old_result['maximum_order'] > 1 else False
            new_addons.execute("""
                                Insert into menu_customization (title,price,
                                maximum_number,description,image,secondary_customization,created_by_id,
                                customization_id,customization_title_id,multiple_selection
            
                                ) 
                                values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                """,
                                    (each_result['title'],each_result['price'],
                                    old_result['maximum_order'],None,each_result['image'],False,vendor_id,None,new_id,multiple_selection)
                                    )
            new_database.commit()
    

        try:
            create_junction = new_database.cursor()
            create_junction.execute("""
                                    Insert Into menu_foodaddonsfoodjunction (categories_id, food_item_id, food_addons_order)
                                    values(%s, %s , %s)
                                        """,
                                        (new_id, food_item_id, 1)
                                        )
            new_database.commit()
        except Exception as e :
            print(e)




            
def create_vendor_food_items(category_id, vendor_id, old_vendor_id, old_category_id,current_user):
    old_vendor_category = old_database.cursor()
    old_vendor_category.execute(f'''
                            select * from menu_fooditem where category_id = {old_category_id[0]}
                            '''
                            )
    food_items = old_vendor_category.fetchall()

    if food_items:
        column_names = [desc[0] for desc in old_vendor_category.description]
        result = [dict(zip(column_names, row)) for row in food_items]
        many_result = result

        many_result = result

        for result in many_result:
            new_user_profile = new_database.cursor()

            new_user_profile.execute("""
                                Insert into menu_fooditem (id,food_title, slug,
                                    description,price, image,is_available,
                                    created_at,updated_at,vendor_id,vendor_categories_id,hours_schedule_id,food_item_order
                                    )
                                    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                    RETURNING id;
                                """,
                                (result['id'],result['food_title'],result['slug'],
                                result['description'],result['price'],result['image'],result['is_available']
                                ,result['created_at'],result['updated_at'],vendor_id,category_id,
                                None,1)
                                )
            food_item_id = new_user_profile.fetchone()
            new_database.commit()

            

            junction_table = old_database.cursor()
            junction_table.execute(f"select id from menu_foodaddonsfoodjunction where food_item_id = '{result['id']}'")
            junction_table_id = junction_table.fetchall()

            create_food_customization(junction_table_id,current_user=current_user, vendor_id = vendor_id, food_item_id = food_item_id[0])
            
            # old_category_id = old_database.cursor()
            # old_category_id.execute(f"select id from menu_category where slug = '{result['slug']}'")
            # old_categry_id = old_category_id.fetchone()

            # create_vendor_food_items(category_id = categry_id,vendor_id=id,old_vendor_id=old_vendor_id, old_category_id =old_categry_id )






def create_vendor_category(email,current_user, id, old_vendor_id):
    old_vendor_category = old_database.cursor()
    old_vendor_category.execute(f'''
                            select * from menu_category where vendor_id = {old_vendor_id}
                            '''
                            )
    old_vendor_category_data = old_vendor_category.fetchall()

    if old_vendor_category_data:
        column_names = [desc[0] for desc in old_vendor_category.description]
        result = [dict(zip(column_names, row)) for row in old_vendor_category_data]
        many_result = result

        for result in many_result:
            new_user_profile = new_database.cursor()

            new_user_profile.execute("""
                                Insert into menu_vendorcategories (category_name, category_slug,
                                    vendor_id,department_id, category_description,active,
                                    tax_rate,tax_exempt,age_restriction,categories_order,hours_schedule_id
                                    )
                                    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                """,
                                (result['category_name'],result['slug'],id,None,result['description'],True,0,False,
                                False,1,None)
                                )
            
            new_database.commit()

            new_food_id = new_database.cursor()
            new_food_id.execute(f"select id from menu_vendorcategories where category_slug = '{result['slug']}'")
            categry_id = new_food_id.fetchone()
            
            old_category_id = old_database.cursor()
            old_category_id.execute(f"select id from menu_category where slug = '{result['slug']}'")
            old_categry_id = old_category_id.fetchone()

            create_vendor_food_items(category_id = categry_id,vendor_id=id,old_vendor_id=old_vendor_id, old_category_id =old_categry_id,current_user=current_user )

def create_vendor(email,current_user, user_profile_id):
    old_user_profile = old_database.cursor()
    old_user_profile.execute(f'''
                            select * from vendor_vendor as up left Join accounts_user as u on up.user_id = u.id
                            where  u.email = '{email}'
                            '''
                            )
    old_user_data = old_user_profile.fetchall()
    if old_user_data:
        column_names = [desc[0] for desc in old_user_profile.description]
        result = [dict(zip(column_names, row)) for row in old_user_data]
        result = result[0]

        new_user_profile = new_database.cursor()

        new_user_profile.execute("""
                                Insert into vendor_vendor (vendor_name, vendor_slug, vendor_license, is_approved, created_at, modified_at, 
                                tax_rate,user_id,user_profile_id ,age_restriction,tax_exempt,vendor_cover_image,vendor_location,
                                vendor_location_latitude,vendor_location_longitude, vendor_logo)
                                    Values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) 
                                    """,
                                    (result['vendor_name'],result['vendor_slug'],result['vendor_license'],result['is_approved'],
                                    result['created_at'],result['modified_at'],result['tax_rate'],current_user,user_profile_id,
                                    False,False,None,None, None,None,None
                                    ) 
                                )
        new_database.commit()
        vendor_id = new_database.cursor()
        old_vendor_id = old_database.cursor()
        vendor_id.execute(f'''
                        select id from vendor_vendor where user_id = {current_user}
                        ''')
        id = vendor_id.fetchone()
        old_vendor_id.execute(
            f"select id from vendor_vendor where vendor_slug = '{result['vendor_slug']}'"
        )
        old_id = old_vendor_id.fetchone()
        old_vendor_id.close()
        create_vendor_category(email, current_user, id[0], old_id[0])
        old_user_profile.close()
        new_user_profile.close()

def create_user_profile(email, current_id):
    
    old_user_profile = old_database.cursor()
    old_user_profile.execute(f'''select * from accounts_userprofile as up left Join accounts_user as u on up.user_id = u.id
                            where  u.email = '{email}'
                            '''
                            )
    old_user_data = old_user_profile.fetchall()
    column_names = [desc[0] for desc in old_user_profile.description]
    result = [dict(zip(column_names, row)) for row in old_user_data]
    result = result[0]
    new_user_profile = new_database.cursor()
    new_user_profile.execute("""
                                Insert into user_userprofile (profile_picture, cover_photo, address, country,state,city,pin_code,latitude,longitude,location,applied_coupon,created_at,modified_at,loyalty_points,user_id)
                                Values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) 
                                """,
                                (result['profile_picture'],result['cover_photo'],result['address'],result['country'],
                                result['state'],result['city'],result['pin_code'],result['latitude'],result['longitude'],
                                result['location'],result['applied_coupon'],result['created_at'],result['modified_at'],0,current_id
                                ) 
                            )

    new_database.commit()
    old_user_profile.close()
    new_user_profile.close()


def create_user_temp_location(email, current_id):
    old_user_profile = old_database.cursor()
    old_user_profile.execute(f'''select * from accounts_usertemporarylocation as up left Join accounts_user as u on up.user_id = u.id
                            where  u.email = '{email}'
                            '''
                            )
    old_user_data = old_user_profile.fetchall()
    if old_user_data:
        column_names = [desc[0] for desc in old_user_profile.description]
        result = [dict(zip(column_names, row)) for row in old_user_data]
        result = result[0]

        new_user_profile = new_database.cursor()

        new_user_profile.execute("""
                                    Insert into user_userlocation (country, state, city, pin_code,latitude,longitude,location,user_id,address,email,first_name,last_name,phone_number)
                                    Values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) 
                                    """,
                                    (result['country'],result['state'],result['city'],"",
                                    result['latitude'],result['longitude'],None,current_id,result['address'],
                                    result['email'],result['first_name'],result['last_name'],result['phone']
                                    ) 
                                )

        new_database.commit()
        new_user_profile.close()
    old_user_profile.close()



def migrate_user_details():
    cur1 = old_database.cursor()
    cur1.execute('''select * from accounts_user;''')
    rows = cur1.fetchall()
    column_names = [desc[0] for desc in cur1.description]
    result = [dict(zip(column_names, row)) for row in rows]
    for each_user in result:
        user_migrate = new_database.cursor()
        user_migrate.execute('''
                INSERT INTO user_user (
                    password, first_name, last_name, username, email, phone_number, role, date_joined, 
                    last_login, created_date, modified_date, is_admin, is_active, is_staff, is_superadmin, first_login
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            ''', (
                each_user['password'], each_user['first_name'], each_user['last_name'], each_user['username'],
                each_user['email'], each_user['phone_number'], each_user['role'], each_user['date_joined'],
                each_user['last_login'], each_user['created_date'], each_user['modified_date'],
                each_user['is_admin'], each_user['is_active'], each_user['is_staff'], each_user['is_superadmin'], False if not (each_user["first_name"] and each_user['last_name']) else True
            ))
        new_database.commit()

        user_migrate.execute(f'''select id from user_user where email='{each_user["email"]}' ''')
        user = user_migrate.fetchone()
        
        create_user_profile(each_user['email'], user[0])
        # print("User Profile migrated")

        create_user_temp_location(each_user['email'], user[0])
        # print("User temporary location migrated")

        user_migrate.execute(f'''select id from user_user where email='{each_user["email"]}' ''')
        user_migrate.execute(f'''
                            select up.id from user_userprofile as up left Join user_user as u on up.user_id = u.id
                            where  u.email = '{each_user['email']}' 
                            ''')
        user_profile = user_migrate.fetchone()

        create_vendor(each_user['email'], user[0], user_profile[0])
        # print("User temporary location migrated")






migrate_user_details()