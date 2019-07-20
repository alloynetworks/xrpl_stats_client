import hashlib
import json

def make_hash(content,mysecret):
    try:
       to_hash = content + mysecret
       hash_object = hashlib.sha256(to_hash.encode())
       hex_digest = hash_object.hexdigest()
       return hex_digest
    except:
       return "None"
