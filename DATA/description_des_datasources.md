
## Dataset principal

**Nom :** Hotel Booking Demand  
**Source :** [Kaggle](https://www.kaggle.com/datasets/jessemostipak/hotel-booking-demand)  
**Fichier :** `hotel_bookings.csv`  
**Taille :** 119 390 enregistrements, 32 colonnes

### Colonnes principales utilisées

| Colonne | Type | Description |
|---------|------|-------------|
| `hotel` | VARCHAR | Type d'hôtel (City Hotel / Resort Hotel) |
| `is_canceled` | BOOLEAN | 1 = annulé, 0 = confirmé |
| `adr` | FLOAT | Average Daily Rate (€) |
| `arrival_date_year` | INT | Année d'arrivée |
| `arrival_date_month` | VARCHAR | Mois d'arrivée |
| `stays_in_week_nights` | INT | Nuits en semaine |
| `stays_in_weekend_nights` | INT | Nuits en week-end |
| `market_segment` | VARCHAR | Canal de réservation |
| `customer_type` | VARCHAR | Type de client |
| `lead_time` | INT | Jours entre réservation et arrivée |


---

## Données de test (schema.sql)

Le fichier `SCRIPTS/schema.sql` contient 10 réservations fictives basées sur de vraies propriétés Marriott pour illustrer le schéma PostgreSQL.
