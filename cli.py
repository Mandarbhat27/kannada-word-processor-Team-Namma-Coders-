# cli.py

from code.word_joiner import WordJoiner


def main():
    wj = WordJoiner()

    print("\n===============================")
    print("   KANNADA WORD JOINER CLI     ")
    print("===============================\n")

    while True:
        print("\nChoose an option:")
        print("1) Apply Sandhi")
        print("2) Apply Vibhakti")
        print("3) Validate Compound Word")
        print("4) Exit")

        choice = input("\nEnter choice (1/2/3/4): ").strip()

        # ---------------------------
        # 1. SANDHI OPTION
        # ---------------------------
        if choice == "1":
            w1 = input("\nEnter first word: ").strip()
            w2 = input("Enter second word: ").strip()
            combined, rule = wj.apply_sandhi(w1, w2)
            print(f"\nResult: {combined}   | Rule used: {rule}")

        # ---------------------------
        # 2. VIBHAKTI OPTION
        # ---------------------------
        elif choice == "2":
            base = input("\nEnter base word: ").strip()
            ending = input("Enter vibhakti ending: ").strip()
            out, vid = wj.apply_vibhakti(base, ending)
            print(f"\nResult: {out}   | Vibhakti ID: {vid}")

        # ---------------------------
        # 3. COMPOUND VALIDATION
        # ---------------------------
        elif choice == "3":
            word = input("\nEnter combined word: ").strip()
            ok, data = wj.validate_compound(word)
            if ok:
                print("\nValid compound word!")
                print(data)
            else:
                print("\nNot found in compound dictionary.")

        # ---------------------------
        # EXIT
        # ---------------------------
        elif choice == "4":
            print("\nExiting...")
            break

        else:
            print("\nInvalid choice. Try again.")

if __name__ == "__main__":
    main()
