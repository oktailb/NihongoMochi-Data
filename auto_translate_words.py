#!/usr/bin/python3
import os
import json
import time
import shutil
from deep_translator import GoogleTranslator

# Configuration
MERGED_FILE = 'shared/src/commonMain/composeResources/files/words/merged_wordlist.json'
OUTPUT_DIR = 'shared/src/commonMain/composeResources/files/words/meanings'
BATCH_SIZE = 50 

LANG_MAP = {
    #'ar_rSA': 'ar',
    'bn_rBD': 'bn', 'de_rDE': 'de', 'en_rGB': 'en',
    'es_rES': 'es', 'fr_rFR': 'fr', 'in_rID': 'id', 'it_rIT': 'it',
    'ko_rKR': 'ko', 'mn_rMN': 'mn', 'pt_rBR': 'pt', 'ru_rRU': 'ru',
    'th_rTH': 'th', 'ua_rUA': 'uk', 'vi_rVN': 'vi', 'zh_rCN': 'zh-CN'
}

def load_json(file_path):
    if not os.path.exists(file_path): return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content: return None
            return json.loads(content)
    except Exception as e:
        # On lève une erreur si le fichier est corrompu pour éviter d'écraser l'existant
        raise Exception(f"ERREUR LECTURE (Fichier corrompu ?) {file_path}: {e}")

def save_json_atomic(file_path, data):
    """Sauvegarde sécurisée : écrit dans un .tmp puis renomme"""
    temp_file = file_path + ".tmp"
    try:
        # Tri systématique par ID pour la cohérence Git
        data['word_meanings']['entries'].sort(key=lambda x: int(x['@id']))
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        shutil.move(temp_file, file_path)
    except Exception as e:
        if os.path.exists(temp_file): os.remove(temp_file)
        print(f"Erreur sauvegarde {file_path}: {e}")

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    merged_data = load_json(MERGED_FILE)
    if not merged_data: 
        print(f"Erreur: {MERGED_FILE} introuvable.")
        return
    words = merged_data.get('words', [])

    # Phase 1 : Initialisation de l'état de chaque langue
    states = {}
    for locale, target_lang in LANG_MAP.items():
        out_file = os.path.join(OUTPUT_DIR, f'word_meanings_{locale}.json')
        
        try:
            data = load_json(out_file)
        except Exception as e:
            print(e)
            return

        if not data:
            data = {"word_meanings": {"@locale": locale, "entries": []}}
        
        # On récupère les IDs déjà présents dans CE fichier spécifiquement
        existing_ids = {str(m['@id']) for m in data['word_meanings'].get('entries', [])}
        
        # File d'attente propre à cette langue
        queue = [w for w in words if str(w['id']) not in existing_ids]
        
        if queue:
            states[locale] = {
                "target_lang": target_lang,
                "out_file": out_file,
                "data": data,
                "queue": queue,
                "total_initial": len(queue),
                "translator": GoogleTranslator(source='ja', target=target_lang)
            }

    if not states:
        print("Toutes les langues sont déjà à jour.")
        return

    print(f"--- Démarrage Round-Robin ({len(states)} langues à traiter) ---")

    round_num = 1
    while states:
        print(f"\n--- Round {round_num} ---")
        locales_finished = []
        
        for locale, state in states.items():
            if not state["queue"]:
                locales_finished.append(locale)
                continue
            
            # On prend le prochain bloc de cette langue
            batch = state["queue"][:BATCH_SIZE]
            texts = [w['text'] for w in batch]
            
            print(f"  [{locale}] {len(texts)} mots... ", end='', flush=True)
            
            try:
                # Traduction Google
                results = state["translator"].translate_batch(texts)
                
                # Ajout des résultats
                for word_obj, translated_text in zip(batch, results):
                    if translated_text:
                        state["data"]['word_meanings']['entries'].append({
                            "@id": str(word_obj['id']),
                            "meaning": translated_text.strip().capitalize()
                        })
                
                # Mise à jour de la queue locale
                state["queue"] = state["queue"][BATCH_SIZE:]
                
                # Sauvegarde immédiate du fichier de la langue
                save_json_atomic(state["out_file"], state["data"])
                
                done = state["total_initial"] - len(state["queue"])
                print(f"OK ({done}/{state['total_initial']})")
                
            except Exception as e:
                print(f"ERREUR: {e} (réessaye au prochain round)")
                # On ne touche pas à la queue en cas d'erreur pour retenter le même bloc
                time.sleep(2)
        
        # Nettoyage des langues terminées
        for l in locales_finished:
            del states[l]
            print(f"  [!] {l} terminé.")
            
        round_num += 1
        time.sleep(1) # Petit délai entre les rounds

    print("\n--- Travail terminé pour toutes les langues ! ---")

if __name__ == "__main__":
    main()
