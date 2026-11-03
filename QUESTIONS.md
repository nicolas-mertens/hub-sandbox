# Vragen

## Modellen, validatie en intervalrekenen (agenda/)

De taak verwijst naar "het contract" en naar de sectie "Invoermodellen" van het masterplan. Die tekst staat nergens in de taak, de repo (alle branches) of `PROGRESS.md`. Ook het tweede acceptatiecriterium is halverwege afgebroken ("… `datetime` waar `d…").

Zonder het contract moet ik de veldnamen, types en validatieregels van `Medewerker`, `Materiaal` en `Boeking` verzinnen. Dat levert een model op waar het vervolg (de boekingslogica) niet op aansluit. Daarom heb ik niets gebouwd.

Nodig:
1. De volledige sectie 'Invoermodellen' en het contract: velden, types, standaardwaarden en publieke namen van `Medewerker`, `Materiaal`, `Boeking`.
2. De volledige tekst van het tweede acceptatiecriterium.
3. De gewenste namen en signaturen van de functies in `intervallen.py` (samenvoegen, aftrekken).

## Klasse Agenda met materiaal op dagniveau (agenda/)

De voorgaande taak (modellen, validatie, intervalrekenen) heeft niets opgeleverd: `agenda/` bevat alleen `fouten.py`. Er zijn geen `Materiaal`, `Boeking`, `Medewerker` of `intervallen.py` om op voort te bouwen. Daarbij staat "de foutentabel" en het contract van het masterplan nergens in de taak of de repo.

Zonder die onderdelen moet ik veldnamen (`beschikbaar`, `middel_id`, `start`, `einde`), types en de rijen van de foutentabel verzinnen. Daarom heb ik niets gebouwd.

Nodig:
1. De opgeleverde modellen (of het contract met velden, types en publieke namen van `Materiaal`, `Medewerker`, `Boeking`).
2. De volledige foutentabel (welke situatie geeft welk uitzonderingstype).
3. Het type van `beschikbaar` (set van data, lijst van periodes?) en van `van`/`tot`/`start`/`einde` bij materiaal (`date`?).
