"""
Szöveges kalandjáték - Arany János Általános Iskola
"""

import random
import time

class KalandJatek:
    def __init__(self):
        self.nev = ""
        self.helyszin = "osztályterem"
        self.targyak = []
        self.pontszam = 0
        self.energia = 100
        
    def lassir(self, szoveg, ido=0.03):
        """Lassan írja ki a szöveget"""
        for betu in szoveg:
            print(betu, end='', flush=True)
            time.sleep(ido)
        print()
    
    def cim(self):
        """Játék címe"""
        print("\n" + "="*60)
        print("   🎒 KALAND AZ ARANY JÁNOS ÁLTALÁNOS ISKOLÁBAN 🎒")
        print("              4/a osztály kalandjai")
        print("="*60 + "\n")
    
    def udvozles(self):
        """Játék indítása"""
        self.cim()
        self.lassir("Üdvözöllek az iskolai kalandjátékban!")
        self.nev = input("\nMi a neved? ")
        self.lassir(f"\nSzia {self.nev}! Készen állsz a kalandra?")
        input("Nyomj ENTER-t a folytatáshoz...")
        print("\n" + "-"*60 + "\n")
    
    def osztályterem(self):
        """Osztályterem helyszín"""
        print("\n📚 OSZTÁLYTEREM - 4/a")
        print("-"*60)
        self.lassir(f"A 4/a osztályban vagy. {self.nev}, az órák már elkezdődtek!")
        self.lassir("A tanító néni éppen magyarázza a matematika leckét.")
        print("\nMit szeretnél csinálni?")
        print("1. Odafigyelek az órára")
        print("2. Átadok egy cetlit a padtársomnak")
        print("3. Kimegyek a folyosóra")
        
        valasztas = input("\nVálassz (1-3): ")
        
        if valasztas == "1":
            self.lassir("\nÜgyesen figyelsz! A tanító néni megdicsér.")
            self.pontszam += 10
            print(f"💫 +10 pont! Összesen: {self.pontszam}")
            self.toriorara()
        elif valasztas == "2":
            self.lassir("\nA tanító néni észreveszi a cetlit!")
            self.lassir("'Vigyázz, mert kiküldelek a folyosóra!' - mondja.")
            self.energia -= 10
            print(f"⚡ Energia: {self.energia}/100")
            self.osztályterem()
        elif valasztas == "3":
            self.folyoso()
        else:
            print("Érvénytelen választás!")
            self.osztályterem()
    
    def toriorara(self):
        """Testnevelés óra"""
        print("\n⚽ TESTNEVELÉS ÓRA - Tornaterem")
        print("-"*60)
        self.lassir("Csengettek! Most tesiórád van.")
        self.lassir("A testnevelő tanár labdajátékot szervez.")
        print("\nMelyik játékot választod?")
        print("1. Focizunk")
        print("2. Kosárlabdázunk")
        print("3. Kimaradok, mert fáj a lábam")
        
        valasztas = input("\nVálassz (1-3): ")
        
        if valasztas == "1":
            self.lassir("\nRemek gólt lősz! A csapatod nyer!")
            self.pontszam += 15
            print(f"⚽ +15 pont! Összesen: {self.pontszam}")
            self.energia += 10
            self.ebedlo()
        elif valasztas == "2":
            self.lassir("\nKosarat dobsz! Szép játék!")
            self.pontszam += 15
            print(f"🏀 +15 pont! Összesen: {self.pontszam}")
            self.energia += 10
            self.ebedlo()
        elif valasztas == "3":
            self.lassir("\nA testnevelő tanár aggódik érted.")
            self.lassir("'Menj el az iskolaorvoshoz!' - mondja.")
            self.iskolaorvos()
        else:
            print("Érvénytelen választás!")
            self.toriorara()
    
    def folyoso(self):
        """Folyosó helyszín"""
        print("\n🚪 FOLYOSÓ")
        print("-"*60)
        self.lassir("A folyosón vagy. Néhány tanár sétál, el kell bújni előlük!")
        self.lassir("A földön egy érdekes tárgyat látsz...")
        
        if random.choice([True, False]):
            self.lassir("Egy régi kulcsot találsz! Felveszed.")
            self.targyak.append("kulcs")
            self.pontszam += 5
            print(f"🔑 Kulcs megszerzve! +5 pont")
        
        print("\nHova mész?")
        print("1. Vissza az osztályterembe")
        print("2. A könyvtárba")
        print("3. Az ebédlőbe")
        
        valasztas = input("\nVálassz (1-3): ")
        
        if valasztas == "1":
            self.osztályterem()
        elif valasztas == "2":
            self.konyvtar()
        elif valasztas == "3":
            self.ebedlo()
        else:
            print("Érvénytelen választás!")
            self.folyoso()
    
    def konyvtar(self):
        """Könyvtár helyszín"""
        print("\n📖 KÖNYVTÁR")
        print("-"*60)
        self.lassir("A csendes könyvtárban vagy. Tele van érdekes könyvekkel.")
        self.lassir("A könyvtáros néni mosolyogva üdvözöl.")
        print("\nMit szeretnél csinálni?")
        print("1. Olvasok egy meséskönyvet")
        print("2. Keresek információt a házifeladathoz")
        print("3. Felfedezem a könyvtár titkos sarkát")
        
        valasztas = input("\nVálassz (1-3): ")
        
        if valasztas == "1":
            self.lassir("\nElmélyülsz a mesevilágban. Csodálatos!")
            self.pontszam += 10
            self.energia += 5
            print(f"📚 +10 pont! Összesen: {self.pontszam}")
            self.ebedlo()
        elif valasztas == "2":
            self.lassir("\nRengeteg hasznos információt találsz!")
            self.pontszam += 15
            print(f"🌟 +15 pont! Összesen: {self.pontszam}")
            self.targyak.append("jegyzet")
            self.ebedlo()
        elif valasztas == "3":
            if "kulcs" in self.targyak:
                self.lassir("\nA kulccsal kinyitsz egy régi szekrényt!")
                self.lassir("Egy régi iskolai kincset találsz benne! 🏆")
                self.pontszam += 30
                print(f"💎 KINCS! +30 pont! Összesen: {self.pontszam}")
                self.targyak.append("kincs")
                self.ebedlo()
            else:
                self.lassir("\nEgy zárral lezárt szekrényt találsz, de nincs hozzá kulcsod.")
                self.ebedlo()
        else:
            print("Érvénytelen választás!")
            self.konyvtar()
    
    def ebedlo(self):
        """Ebédlő helyszín"""
        print("\n🍽️ ISKOLAI EBÉDLŐ")
        print("-"*60)
        self.lassir("Az ebédlőben vagy. Finom illatok érkeznek a konyhából.")
        self.lassir("Ma rántott hús, rizs és uboroka van.")
        print("\nMit csinálsz?")
        print("1. Jóízűen megeszem az ebédet")
        print("2. Csak a desszertet kérem")
        print("3. Segítek az asztalokat letörölni")
        
        valasztas = input("\nVálassz (1-3): ")
        
        if valasztas == "1":
            self.lassir("\nFinom volt az ebéd! Erőre kaptál.")
            self.energia = min(100, self.energia + 20)
            self.pontszam += 5
            print(f"⚡ Energia feltöltve: {self.energia}/100")
            self.udvaro()
        elif valasztas == "2":
            self.lassir("\nA konyhásnéni csóválja a fejét, de adott palacsintát.")
            self.energia += 5
            self.udvaro()
        elif valasztas == "3":
            self.lassir("\nMilyen segítőkész vagy! A konyhásnéni megköszöni.")
            self.pontszam += 15
            self.energia += 10
            print(f"❤️ +15 pont! Összesen: {self.pontszam}")
            self.udvaro()
        else:
            print("Érvénytelen választás!")
            self.ebedlo()
    
    def iskolaorvos(self):
        """Iskolaorvos"""
        print("\n⚕️ ISKOLAORVOS")
        print("-"*60)
        self.lassir("Az iskolaorvos megvizsgál.")
        self.lassir("'Semmi baj, csak pihenj egy kicsit!' - mondja.")
        self.energia = min(100, self.energia + 30)
        print(f"⚡ Energia: {self.energia}/100")
        self.ebedlo()
    
    def udvaro(self):
        """Iskolaudvar - szünet"""
        print("\n🌳 ISKOLAUDVAR - Szünet")
        print("-"*60)
        self.lassir("Szünet van! Az udvaron vagy az osztálytársaiddal.")
        self.lassir("Mindenki játszik és beszélget.")
        print("\nMivel töltöd a szünetet?")
        print("1. Focizok a többiekkel")
        print("2. Beszélgetek a barátaimmal")
        print("3. Felfedezem az iskola kertjét")
        
        valasztas = input("\nVálassz (1-3): ")
        
        if valasztas == "1":
            self.lassir("\nÜgyes driblingsekkel gólt lősz!")
            self.pontszam += 10
            print(f"⚽ +10 pont! Összesen: {self.pontszam}")
            self.vege()
        elif valasztas == "2":
            self.lassir("\nJó beszélgetésetek van a barátaiddal!")
            self.pontszam += 10
            print(f"😊 +10 pont! Összesen: {self.pontszam}")
            self.vege()
        elif valasztas == "3":
            self.lassir("\nAz iskola kertjében egy szép virágoskertet találsz.")
            self.lassir("A gondnok bácsi megmutatja a különleges növényeket.")
            self.pontszam += 20
            print(f"🌺 +20 pont! Összesen: {self.pontszam}")
            self.vege()
        else:
            print("Érvénytelen választás!")
            self.udvaro()
    
    def vege(self):
        """Játék vége"""
        print("\n" + "="*60)
        print("                    🎓 ISKOLA VÉGE! 🎓")
        print("="*60)
        self.lassir(f"\nVége a mai iskolai napnak, {self.nev}!")
        self.lassir("Hazamehetsz!")
        print(f"\n📊 VÉGSŐ EREDMÉNYED:")
        print(f"   💫 Pontszám: {self.pontszam}")
        print(f"   ⚡ Energia: {self.energia}/100")
        print(f"   🎒 Megszerzett tárgyak: {', '.join(self.targyak) if self.targyak else 'Nincs'}")
        
        # Értékelés
        if self.pontszam >= 80:
            print(f"\n🏆 Kitűnő! Te vagy a hét tanulója!")
        elif self.pontszam >= 60:
            print(f"\n⭐ Nagyon jól teljesítettél!")
        elif self.pontszam >= 40:
            print(f"\n👍 Jó munka! Szép volt a napod!")
        else:
            print(f"\n😊 Holnap újra próbálkozhatsz!")
        
        print("\n" + "="*60)
        print("Köszönjük, hogy játszottál!")
        print("="*60 + "\n")
        
        # Újrajátszás
        ujra = input("Szeretnél újra játszani? (i/n): ").lower()
        if ujra == 'i':
            self.__init__()
            self.jatek_inditasa()
    
    def jatek_inditasa(self):
        """Játék indítása"""
        self.udvozles()
        self.osztályterem()


def main():
    """Főprogram"""
    jatek = KalandJatek()
    jatek.jatek_inditasa()


if __name__ == "__main__":
    main()
