"""生成 bcrypt 哈希：python scripts/gen_hash.py <password>"""
import sys

from passlib.context import CryptContext

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python scripts/gen_hash.py <password>")
        raise SystemExit(1)
    print(CryptContext(schemes=["bcrypt"], deprecated="auto").hash(sys.argv[1]))
