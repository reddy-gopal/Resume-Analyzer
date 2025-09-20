# gen_hashes.py
from streamlit_authenticator.utilities.hasher import Hasher

passwords = [ "password"]
hashed_passwords = Hasher.hash_list(passwords)   # <-- use hash_list, not .generate()
print(hashed_passwords)
