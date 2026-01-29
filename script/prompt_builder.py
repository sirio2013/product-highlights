def build_prompt(product_id: int, title: str, description: str, highlights: dict[str, list[str]]) -> str:
    """Build a prompt for selecting the most relevant product highlights."""
    prompt = (
        "<ruolo>\n"
        "Sei un esperto di marketing per prodotti pet care. "
        "Il tuo compito e' analizzare la descrizione di un prodotto e "
        "selezionare i product highlights piu' pertinenti tra quelli proposti.\n"
        "</ruolo>\n\n"
    )

    prompt += f"<descrizione-prodotto>{description}</descrizione-prodotto>\n\n"

    for key, values in highlights.items():
        values_str = "\n".join(f"- {v}" for v in values)
        prompt += f"<{key}>\n{values_str}\n</{key}>\n\n"

    prompt += (
        "<richiesta>\n"
        "Leggi il contenuto del tag 'descrizione-prodotto'. "
        "Per ciascuno dei tre gruppi di product-highlights, "
        "seleziona esattamente UN valore (senza modificarlo) "
        "che sia il piu' pertinente rispetto alla descrizione del prodotto.\n"
        "</richiesta>\n\n"
        "<istruzioni>\n"
        "1. Per ciascun gruppo (product-highlights-1, product-highlights-2, product-highlights-3), "
        "fai un ranking di tutti i valori dal piu' pertinente al meno pertinente.\n"
        "2. Per ogni ranking, spiega brevemente il motivo della classifica.\n"
        "3. Seleziona il valore al primo posto di ciascun ranking.\n"
        "4. Riscrivi la descrizione originale inserendo naturalmente nel testo "
        "tutti e tre i product-highlights selezionati (1, 2 e 3). "
        "Integra ciascun highlight nel punto piu' appropriato del testo, "
        "come parte naturale del discorso.\n"
        "5. Mantieni ESATTAMENTE il testo della descrizione originale: "
        "limitati SOLO ad integrare i product-highlights selezionati "
        "(ESATTAMENTE lo stesso testo); se necessario riscrivi la frase, "
        "importante che il product-highlight sia integrato verbatim.\n"
        "6. Se trovi errori di battitura o spazi in eccesso nella descrizione originale, correggili.\n"
        "7. Il formato di output deve essere HTML (senza titoli, senza bullet point, senza heading). "
        "Testo piano in HTML.\n"
        "8. Restituisci il risultato finale ESCLUSIVAMENTE come dizionario JSON "
        "con il seguente formato:\n"
        "{\n"
        f'  "id": {product_id},\n'
        f'  "titolo": "{title}",\n'
        '  "descrizione-iniziale": "<descrizione originale senza modifiche>",\n'
        '  "product-highlights-1": "<valore scelto>",\n'
        '  "product-highlights-2": "<valore scelto>",\n'
        '  "product-highlights-3": "<valore scelto>",\n'
        '  "descrizione": "<descrizione originale con i 3 highlights integrati, in formato HTML>"\n'
        "}\n"
        "</istruzioni>"
    )

    return prompt


if __name__ == "__main__":
    from data_import import import_products, import_highlights

    df = import_products()
    highlights = import_highlights()

    first = df.iloc[0]
    prompt = build_prompt(first["id"], first["title"], first["description"], highlights)
    print(prompt)
