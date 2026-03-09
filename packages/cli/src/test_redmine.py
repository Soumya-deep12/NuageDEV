from nuage import config, redmine
print("Testing update...")
res = redmine.update_issue_status("https://192.168.0.3", "b1178d6a6ad5fe3b25f616fc4801cd9679af4503", 6926, 3)
print(f"Result: {res}")
