import database
database.init_db()
print(database.create_session("Test Session"))
print(database.get_coach_sessions())
