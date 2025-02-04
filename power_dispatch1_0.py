# Import required libraries
import gurobipy as gp
from gurobipy import GRB

# Define parameters
Tau = 6  # Number of dispatch periods
S = 4  # Number of scenarios
G = 5  # Number of generators
P_s = [0.6] * S  # Probability of contingency scenario s

# Cost parameters
C_cur = 50  # Cost of wind curtailment
C_she = 100  # Cost of load shedding
fuel_cost = {g: 30 for g in range(G)}  # Fuel costs for each generator
C_ug = 100  # Start-up cost
C_dg = 80  # Shut-down cost
U_D_Rg = 50  # Ramp rate limits

# BESS parameters
BESS_capacity = 60
eta_charge = 0.9
eta_discharge = 0.9

# Wind uncertainty set parameters
mu_t = [100] * Tau  # Example mean forecast
Gamma_1, Gamma_2 = 10, 5  # Uncertainty set bounds

# Initialize the model
model = gp.Model("DMSR")

# Decision variables
Pg = model.addVars(Tau, S, G, vtype=GRB.CONTINUOUS, name="Pg")  # Generator output
u = model.addVars(Tau, S, G, vtype=GRB.BINARY, name="u")         # FA unit state
s_ug = model.addVars(Tau, S, G, vtype=GRB.BINARY, name="StartUp")  # Start-up indicator
s_dg = model.addVars(Tau, S, G, vtype=GRB.BINARY, name="ShutDown")  # Shut-down indicator
SoC = model.addVars(Tau, S, vtype=GRB.CONTINUOUS, name="SoC")  # BESS state of charge
Pw = model.addVars(Tau, S, vtype=GRB.CONTINUOUS, name="Pw")  # Wind power utilized
Pz = model.addVars(Tau, S, vtype=GRB.CONTINUOUS, name="Pz")  # Load shedding

# Objective function
objective = gp.quicksum(
    fuel_cost[g] * Pg[t, s, g] +
    C_ug * s_ug[t, s, g] +
    C_dg * s_dg[t, s, g] +
    C_cur * (mu_t[t] - Pw[t, s]) +  # Wind curtailment cost
    C_she * Pz[t, s]               # Load shedding cost
    for g in range(G) for t in range(Tau) for s in range(S)
)
model.setObjective(objective, GRB.MINIMIZE)

# Constraints
# 1. Generation limits
model.addConstrs(
    Pg[t, s, g] <= 100 * u[t, s, g] for g in range(G) for t in range(Tau) for s in range(S)
)

# 2. Power balance
model.addConstrs(
    gp.quicksum(Pg[t, s, g] for g in range(G)) +
    Pw[t, s] +
    SoC[t, s] == mu_t[t] + Pz[t, s]
    for t in range(Tau) for s in range(S)
)

# 3. Ramp rate constraints
model.addConstrs(
    Pg[t + 1, s, g] - Pg[t, s, g] <= U_D_Rg for g in range(G) for t in range(Tau - 1) for s in range(S)
)
model.addConstrs(
    Pg[t, s, g] - Pg[t + 1, s, g] <= U_D_Rg for g in range(G) for t in range(Tau - 1) for s in range(S)
)

# 4. Start-up and shut-down logic
model.addConstrs(
    s_ug[t, s, g] >= u[t, s, g] - u[t - 1, s, g] for g in range(G) for t in range(1, Tau) for s in range(S)
)
model.addConstrs(
    s_dg[t, s, g] >= u[t - 1, s, g] - u[t, s, g] for g in range(G) for t in range(1, Tau) for s in range(S)
)

# 5. BESS constraints
model.addConstrs(SoC[t, s] >= 0 for t in range(Tau) for s in range(S))
model.addConstrs(SoC[t, s] <= BESS_capacity for t in range(Tau) for s in range(S))
model.addConstrs(
    SoC[t, s] == SoC[t - 1, s] - Pw[t, s] * eta_discharge + Pw[t, s] / eta_charge
    for t in range(1, Tau) for s in range(S)
)

# Solve the model
model.optimize()

# Retrieve results
if model.status == GRB.OPTIMAL:
    for t in range(Tau):
        for s in range(S):
            print(f"Period {t}, Scenario {s}:")
            for g in range(G):
                print(f"  Generator {g}: Pg = {Pg[t, s, g].x}")
            print(f"  Wind Power Used: Pw = {Pw[t, s].x}")
            print(f"  Load Shedding: Pz = {Pz[t, s].x}")
            print(f"  SoC = {SoC[t, s].x}")
