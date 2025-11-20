-- 1) UTILISATEUR
INSERT INTO utilisateur (id_utilisateur, nom, prenom, telephone, email, mot_de_passe, administrateur)
VALUES
(1, 'Dupont', 'Alice', '0601020304', 'alice.dupont@email.com', '$2b$12$fZE56Wsei2WahQDwQeGqTuk5UV0STIDWHmfckEYQMskVzKRCFFV7q', FALSE),
(2, 'Martin', 'Bob', '0605060708', 'bob.martin@email.com', '$2b$12$ZI9goAGUifVgF7dcZbNvgOjKED/Bfo193c5BDQW5RSaNxvkqu9QYa', TRUE),
(3, 'Durand', 'Caroline', '0608091011', 'caroline.durand@email.com', '$2b$12$T5xxw5LIJUv1YuYuIedUguUpNA7MNpJDXIZCpDrl4fUViE2K3itMq', FALSE),
(4, 'Petit', 'David', '0611121314', 'david.petit@email.com', '$2b$12$qYjWLSa6VwcE.Ex9MoABGOyaAQME3K7wZiO/VIFRSWjKnwFcxZvnC', FALSE)
ON CONFLICT (id_utilisateur) DO NOTHING;

-- Utilisateur pour les tests de suppression
INSERT INTO utilisateur (id_utilisateur, nom, prenom, email, mot_de_passe, administrateur)
VALUES
(5, 'A_Supprimer', 'Test', 'delete@me.com', '$2b$12$qYjWLSa6VwcE.Ex9MoABGOyaAQME3K7wZiO/VIFRSWjKnwFcxZvnC', FALSE)
ON CONFLICT (id_utilisateur) DO NOTHING;

---
---
-- 2) EVENEMENT
-- Tous créés par l'Admin (Bob, ID 2)
-- Les capacités sont celles du LIEU
INSERT INTO evenement (id_evenement, fk_utilisateur, titre, adresse, ville, date_evenement, description, capacite, categorie, statut)
VALUES
(1, 2, 'Conférence Tech', '10 Rue de Paris', 'Lyon', '2025-11-30', 'Événement sur les nouvelles technologies.', 30, 'Technologie', 'disponible en ligne'),
(2, 2, 'Salon de l’Art', '5 Avenue de Nice', 'Nice', '2025-12-01', 'Exposition art contemporain.', 50, 'Art', 'disponible en ligne'),
(3, 2, 'Match de Football', 'Stade National', 'Bruxelles', '2025-12-02', 'Rencontre sportive locale.', 100, 'Sport', 'disponible en ligne'),
(4, 2, 'Festival de Musique', 'Parc Central', 'Toulouse', '2025-12-03', 'Concert en plein air.', 60, 'Musique', 'disponible en ligne')
ON CONFLICT (id_evenement) DO NOTHING;

---
---
-- 3) BUS
-- Les capacités des bus sont LOGIQUES par rapport à l'événement
INSERT INTO bus (fk_evenement, matricule, nombre_places, direction, description)
VALUES
-- Evt 1 (Lieu=30) : Le bus a 30 places.
(1, 'BUS-001', 30, 'aller',  'Bus 1 aller (Départ 18h Rennes)'),
(1, 'BUS-002', 30, 'retour', 'Bus 1 retour (Départ 02h Lyon)'),

-- Evt 2 (Lieu=50) : Le bus a 50 places.
(2, 'BUS-003', 50, 'aller',  'Bus 2 aller'),
(2, 'BUS-004', 50, 'retour', 'Bus 2 retour'),

-- Evt 3 (Lieu=100) : Le bus a 75 places (moins que le lieu).
(3, 'BUS-005', 75, 'aller',  'Bus 3 aller'),
(3, 'BUS-006', 75, 'retour', 'Bus 3 retour'),

-- Evt 4 (Lieu=60) : L'admin n'a pas prévu de bus retour.
(4, 'BUS-007', 50, 'aller',  'Bus 4 aller');

---
---
-- 4) RESERVATION
INSERT INTO reservation (id_reservation, fk_utilisateur, fk_evenement, bus_aller, bus_retour, adherent, sam, boisson)
VALUES
-- Alice (ID 1) va à l'Evt 1 (Lieu=30, Bus=30)
(1, 1, 1, TRUE,  TRUE,  TRUE,  FALSE, TRUE),
-- Caroline (ID 3) va à l'Evt 2 (Lieu=50, Bus=50)
(2, 3, 2, FALSE, FALSE, TRUE,  FALSE, FALSE),
-- David (ID 4) va à l'Evt 3 (Lieu=100, Bus=75)
(3, 4, 3, TRUE,  FALSE, TRUE,  TRUE,  FALSE)
ON CONFLICT (id_reservation) DO NOTHING;

---
---
-- 5) COMMENTAIRE
INSERT INTO commentaire (fk_reservation, fk_utilisateur, note, avis)
VALUES
(1, 1, 5, 'Voyage très agréable.'),
(2, 3, 4, 'Bon service.'),
(3, 4, 3, 'Moyen, le bus était un peu vieux.');


-- IMPORTANT : Mise à jour des compteurs SERIAL pour les tests
-- (Pour éviter les 'UniqueViolation' sur les ID)
SELECT setval(pg_get_serial_sequence('utilisateur', 'id_utilisateur'), (SELECT MAX(id_utilisateur) FROM utilisateur));
SELECT setval(pg_get_serial_sequence('evenement', 'id_evenement'), (SELECT MAX(id_evenement) FROM evenement));
SELECT setval(pg_get_serial_sequence('bus', 'id_bus'), (SELECT MAX(id_bus) FROM bus));
SELECT setval(pg_get_serial_sequence('reservation', 'id_reservation'), (SELECT MAX(id_reservation) FROM reservation));
SELECT setval(pg_get_serial_sequence('commentaire', 'id_commentaire'), (SELECT MAX(id_commentaire) FROM commentaire));