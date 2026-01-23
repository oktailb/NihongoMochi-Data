#!/usr/bin/python3
import os
import glob
import time

# Configuration
BASE_DIR = 'langs'

def main():
    # Liste des fichiers source (ceux à la racine de SOURCE_DIR)
    langs = glob.glob(os.path.join(BASE_DIR, "*"))
    
    for lang in langs:
        lang = lang.replace('langs/', '')
        print(f"--- Packaging de '{lang}' ---")
        os.system(f"cd {BASE_DIR}/{lang}/grammar ; zip -q -9 ../grammar.zip *.html ; cd -")
        os.system(f"cd {BASE_DIR}/{lang}/ ; zip -q -9 ./data.zip *.json ; cd -")

if __name__ == "__main__":
    main()
