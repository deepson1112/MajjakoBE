import hmac
import hashlib
import base64

def generate_esewa_signature(secret_key, total_amount, transaction_uuid, product_code):
    # Create the message to be hashed
    message = f'total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}'
    hash_object = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    hash_digest = hash_object.digest()
    signature = base64.b64encode(hash_digest).decode('utf-8')
    return signature
