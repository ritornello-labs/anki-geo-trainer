# GeoTrainer public packs

Historical candidate built 2026-09-30 from the sanitized public source. Its identity/union checks and real-Anki overlapping import smoke passed for that candidate only. **Superseded October 3: publication scope is under reconciliation and the full-edition preview is withdrawn.** Components will ship first and the full edition last. See [scope reconciliation](SCOPE_RECONCILIATION_2026-10-03.md). Elvis approved the existing listing’s full-edition assignment on September 30; original share name `GeoTrainer` is verified, but [actual legacy import compatibility fails](FULL_LEGACY_IMPORT_2026-10-05.md). All fifteen components are submitted; the full update remains held.

The September 30 candidate contained 2,651 notes / 2,673 cards; these are not final release counts. Every pack uses the same scope model IDs, leaf deck IDs, GUIDs, fields, and templates as the full edition. The eight physical-systems QA scopes and the foundations prototype are excluded.

World countries includes the accepted Continents silhouette drills alongside the six continent country scopes. Country subdivision packs cover the ten countries already supported; no new country content is invented.

The following counts describe the superseded candidate, not approved shipping artifacts. Surface ocean currents have since been withheld; accepted membership/concept inclusion is being reconciled.

| Historical candidate | Notes | Cards |
|---|---:|---:|
| geo-trainer-argentina-subdivisions.apkg | 96 | 96 |
| geo-trainer-australia-subdivisions.apkg | 35 | 35 |
| geo-trainer-brazil-subdivisions.apkg | 108 | 108 |
| geo-trainer-canada-subdivisions.apkg | 52 | 52 |
| geo-trainer-china-subdivisions.apkg | 124 | 124 |
| geo-trainer-india-subdivisions.apkg | 140 | 140 |
| geo-trainer-indonesia-subdivisions.apkg | 131 | 131 |
| geo-trainer-islands-archipelagos.apkg | 67 | 67 |
| geo-trainer-mexico-subdivisions.apkg | 128 | 128 |
| geo-trainer-physical-geography.apkg | 284 | 284 |
| geo-trainer-plate-tectonics.apkg | 132 | 132 |
| geo-trainer-reference-lines-time.apkg | 56 | 78 |
| geo-trainer-russia-subdivisions.apkg | 333 | 333 |
| geo-trainer-united-states-subdivisions.apkg | 200 | 200 |
| geo-trainer-world-countries.apkg | 765 | 765 |

Build: `python scripts/build_apkg.py --public-packs`. Reference/time maps require the Timezone Boundary Builder 2026d input described in `data/SOURCES.md`. Keep the existing share name exactly when updating 908455862; Elvis approved its full-edition assignment on 2026-09-30; its exact original share name still needs verification.
