===========================
DOCUMENTAZIONE TIPI DI DATI
===========================

Questa documentazione descrive i tipi di dati supportati dal programma per la decodifica dei pacchetti UDP, inclusi i nuovi tipi aggiunti.

--------------------------------------
TIPI DI DATI ATTUALMENTE SUPPORTATI
--------------------------------------

1. FLOAT (`float`)
   - Dimensione: 4 byte
   - Descrizione: Numero in virgola mobile a precisione singola.
   - Codifica: IEEE 754.
   - Esempio: 3.14.

2. INT (`int`)
   - Dimensione: 4 byte
   - Descrizione: Numero intero con segno.
   - Range: Da -2,147,483,648 a 2,147,483,647.

3. UNSIGNED 8-BIT INTEGER (`uint_8`)
   - Dimensione: 1 byte
   - Descrizione: Numero intero senza segno.
   - Range: Da 0 a 255.

4. SIGNED 8-BIT INTEGER (`int_8`)
   - Dimensione: 1 byte
   - Descrizione: Numero intero con segno.
   - Range: Da -128 a 127.

5. UNSIGNED 16-BIT INTEGER (`uint_16`)
   - Dimensione: 2 byte
   - Descrizione: Numero intero senza segno.
   - Range: Da 0 a 65,535.

6. SIGNED 16-BIT INTEGER (`int_16`)
   - Dimensione: 2 byte
   - Descrizione: Numero intero con segno.
   - Range: Da -32,768 a 32,767.

7. UNSIGNED 32-BIT INTEGER (`uint_32`)
   - Dimensione: 4 byte
   - Descrizione: Numero intero senza segno.
   - Range: Da 0 a 4,294,967,295.

8. SIGNED 32-BIT INTEGER (`int_32`)
   - Dimensione: 4 byte
   - Descrizione: Numero intero con segno.
   - Range: Da -2,147,483,648 a 2,147,483,647.

9. UNSIGNED 64-BIT INTEGER (`uint_64`)
   - Dimensione: 8 byte
   - Descrizione: Numero intero senza segno.
   - Range: Da 0 a 18,446,744,073,709,551,615.

10. SIGNED 64-BIT INTEGER (`int_64`)
    - Dimensione: 8 byte
    - Descrizione: Numero intero con segno.
    - Range: Da -9,223,372,036,854,775,808 a 9,223,372,036,854,775,807.

11. DOUBLE (`double`)
    - Dimensione: 8 byte
    - Descrizione: Numero in virgola mobile a doppia precisione.
    - Codifica: IEEE 754.
    - Esempio: 3.14159265359.

12. CARATTERE (`char`)
    - Dimensione: 1 byte
    - Descrizione: Carattere singolo ASCII.
    - Esempio: 'A'.

13. STRINGA (`string`)
    - Dimensione: Variabile (terminata con \x00).
    - Descrizione: Sequenza di caratteri ASCII.
    - Esempio: "Hello".

14. BOOLEANO (`bool`)
    - Dimensione: 1 byte.
    - Descrizione: Valore booleano (True o False).
    - Esempio: 1 (True), 0 (False).

15. BIT SPECIFICO (`bit_X`)
    - Dimensione: 1 bit (indicato con `_X`, dove `X` è l'indice del bit).
    - Descrizione: Valore booleano estratto da un byte specifico.
    - Esempio: bit_3 legge il 4° bit di un byte.

16. BCD (Binary-Coded Decimal) (`bcd`)
    - Dimensione: 1 byte.
    - Descrizione: Valore numerico rappresentato in formato BCD (Binary-Coded Decimal).
    - Esempio: 0x12 rappresenta il numero decimale 12.

17. TIMESTAMP UNIX (`timestamp`)
    - Dimensione: 4 o 8 byte.
    - Descrizione: Valore temporale in secondi (32-bit) o nanosecondi (64-bit) dall'Epoca Unix (1° gennaio 1970).
    - Esempio: 1697040000 rappresenta una data e un'ora specifica.

18. ARRAY DI BYTE (`byte_array`)
    - Dimensione: Variabile.
    - Descrizione: Sequenza grezza di byte.
    - Esempio: [0x12, 0x34, 0x56].

--------------------------------------
COME AGGIUNGERE NUOVI TIPI DI DATI
--------------------------------------

1. Apri il metodo `process_data` nel codice.
2. Aggiungi un nuovo controllo nel blocco `elif` per il tipo di dato desiderato.
3. Usa `struct.unpack_from` o un metodo personalizzato per interpretare i dati.

Esempio per un tipo personalizzato:
```python
elif data_type == 'new_type':
    value = struct.unpack_from('<formato>', data, offset)[0]
