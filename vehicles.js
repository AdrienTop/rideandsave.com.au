// ============================================================
// VEHICLE DATA — estimated real-world L/100km
// Official figures: NZTA Motor Vehicle Register (Fleet.csv)
// Real-world gap: EU Commission OBFCM report, March 2024
//   Petrol: +23.7% over WLTP   Diesel: +18.1% over WLTP   Hybrid: +14%
//   Source: 600,000 vehicles, 2021 on-board monitoring
// Rankings by AU registered fleet (BITRE Road Vehicles Australia 2024)
// ============================================================

const VD = {
  small:    { icon:'🚗', name:'Small car',    sub:'Corolla · Mazda 3 · i30',      fuels:['petrol'],           default:'petrol',  cons:{petrol:7.7},              maint:0.07 },
  medium:   { icon:'🚘', name:'Medium car',   sub:'Camry · Outback · Mazda 6',   fuels:['petrol'],           default:'petrol',  cons:{petrol:9.5},              maint:0.08 },
  small_suv:{ icon:'🚙', name:'Small SUV',    sub:'ASX · CX-3 · Kona',           fuels:['petrol'],           default:'petrol',  cons:{petrol:8.5},              maint:0.09 },
  large_suv:{ icon:'🚙', name:'Large SUV',    sub:'RAV4 · CX-5 · Forester',      fuels:['petrol','diesel'],  default:'petrol',  cons:{petrol:9.1,diesel:7.4},   maint:0.10 },
  fourwd:   { icon:'4x4',  name:'4WD',        sub:'LandCruiser · Prado · Patrol', fuels:['diesel','petrol'], default:'diesel',  cons:{diesel:10.3,petrol:14.9}, maint:0.11 },
  ute:      { icon:'🛻', name:'Ute',          sub:'HiLux · Ranger · Triton',     fuels:['diesel','petrol'],  default:'diesel',  cons:{diesel:9.3,petrol:13.6},  maint:0.12 },
  van:      { icon:'🚐', name:'Van',          sub:'HiAce · Carnival · iLoad',    fuels:['diesel','petrol'],  default:'diesel',  cons:{diesel:9.2,petrol:13.0},  maint:0.12 },
  hybrid:   { icon:'🔋', name:'Hybrid',       sub:'RAV4 H · Camry H · Corolla H', fuels:['petrol'],          default:'petrol',  cons:{petrol:5.0},              maint:0.09 },
  electric: { icon:'⚡', name:'Electric',     sub:'Model 3 · Model Y · BYD',     fuels:['electric'],         default:'electric', cons:{electric:17.0},          maint:0.04 },
  custom:   { icon:'✏️', name:'Custom',       sub:'Your consumption',            fuels:['petrol','diesel','electric'], default:'petrol', cons:{petrol:0,diesel:0,electric:0}, maint:0.08 },
};

// CO2 emission factors by fuel type (kg CO2 per litre burned)
// Source: Department of Climate Change, Energy, the Environment and Water (DCCEEW)
const CO2_FACTOR = { petrol: 2.310, diesel: 2.640, electric: 0 };

// ATO 2025–26 cents per kilometre rate — single flat rate, all vehicle types
// No separate rates by fuel type (unlike NZ IRD)
// Source: ato.gov.au — cents per kilometre method
const ATO_RATE = 0.88;
