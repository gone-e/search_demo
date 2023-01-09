import base64
import boto3
from airflow.models import Variable
from aws.s3.aws_s3 import AwsS3


aws = Variable.get(
    "aws",
    deserialize_json=True,
    default_var={"kms": {"key_id": "c0b9195d-668b-440e-925d-05c986b07b4a"}},
)


class AWSCipher(object):
    def __init__(self):
        self.client = boto3.client("kms", region_name="ap-northeast-2")
        self.cipher = self.ciphertext_blob
        self.iv = "3874716971143874".encode("utf-8")

    @property
    def ciphertext_blob(self):
        cipher_file = "cipher.key"
        s3 = AwsS3("oh-mgmt-security-key-s3")
        s3.download_file(cipher_file, "prod_cipher.key")

        with open(cipher_file, "r") as f:
            return str(f.read())

    @property
    def kms(self):
        return aws.get("kms")

    def pad(self, s, fill_char, plaintext_length, plain_text):
        return s + bytes([fill_char]) * (plaintext_length - len(plain_text))

    def encrypt_data(self, plaintext_message):
        from Crypto.Cipher import AES

        BS = AES.block_size
        plaintext_length = len(plaintext_message)
        fill_char = BS - (plaintext_length % BS)

        if plaintext_length % BS != 0:
            plaintext_length = plaintext_length + (BS - (plaintext_length % BS))

        plain_text = plaintext_message.encode("utf-8")
        # pad = lambda s: s + bytes([fill_char]) * (plaintext_length - len(plain_text))

        decrypted_key = self.client.decrypt(
            CiphertextBlob=base64.decodestring(self.cipher.encode("utf-8"))
        ).get("Plaintext")
        crypter = AES.new(decrypted_key, AES.MODE_CBC, IV=self.iv)
        encrypted_data = base64.b64encode(
            crypter.encrypt(
                self.pad(plain_text, fill_char, plaintext_length, plain_text)
            )
        )

        return encrypted_data

    def decrypt_data(self, encrypted_data):
        from Crypto.Cipher import AES

        decrypted_key = self.client.decrypt(
            CiphertextBlob=base64.decodestring(self.cipher.encode("utf-8"))
        ).get("Plaintext")
        crypter = AES.new(decrypted_key, AES.MODE_CBC, IV=self.iv)
        return crypter.decrypt(base64.b64decode(encrypted_data)).rstrip()


if __name__ == "__main__":
    test = AWSCipher()

    base64_enc_data = "eLg8mrDgF/bsjJqUMlN41iMQxkWgEh8xuCeROX+vtR0=".encode("utf-8")
    base64_dec_data = test.decrypt_data(base64_enc_data)
    print(base64_dec_data)
    print(base64_dec_data.decode("utf-8"))
    print(test.encrypt_data("hohyun82@email.com").decode("utf-8"))
