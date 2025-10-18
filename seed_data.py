from main import SessionLocal, Clause

db = SessionLocal()

sample_data = [
    Clause(clause_id="300.2", heading="Definitions", summary="Contains key definitions for terms used in the Code.", edition_year="2024"),
    Clause(clause_id="302.2.4", heading="Allowable Stress", summary="Specifies allowable stress values for materials.", edition_year="2024"),
]

db.add_all(sample_data)
db.commit()
db.close()

print("✅ Sample clauses inserted.")
