# Import required libraries
import gurobipy as gp
from gurobipy import GRB

# Define parameters
Tau = 3  # Number of dispatch periods
S = 10  # Number of scenarios
G = 5  # Number of generators
P_s = [0.1] * S  # Probability of contingency scenario s

# Cost parameters
C_cur = 50  # Cost of wind curtailment and load shedding
fuel_cost = {g: 100 for g in range(G)}  # Example fuel costs for each generator
C_ug = 500  # Start-up cost of unit g
C_dg = 400  # Shut-down cost of unit g
U_D_Rg = 50  # Ramp rate limits of unit g

# Wind uncertainty set parameters
mu_t = [50] * Tau  # Example mean forecast
Gamma_1, Gamma_2 = 10, 5  # Uncertainty set bounds

# Initialize the model
model = gp.Model("DMSR")

# Define decision variables
Pg = model.addVars(Tau, S, G, vtype=GRB.CONTINUOUS, name="Pg")  # Generator output
u = model.addVars(Tau, S, G, vtype=GRB.BINARY, name="u")         # FA unit state
SoC = model.addVars(Tau, S, vtype=GRB.CONTINUOUS, name="SoC")    # BESS state of charge
s_ug = model.addVars(Tau, S, G, vtype=GRB.BINARY, name="StartUp")  # Start-up indicator
s_dg = model.addVars(Tau, S, G, vtype=GRB.BINARY, name="ShutDown")  # Shut-down indicator

# Define objective function
objective = gp.quicksum(
    fuel_cost[g] * Pg[t, s, g] +
    C_ug * s_ug[t, s, g] +
    C_dg * s_dg[t, s, g]
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
    SoC[t, s] == mu_t[t]
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
model.addConstrs(SoC[t, s] <= 100 for t in range(Tau) for s in range(S))  # Example capacity limit

# Solve the model
model.optimize()

# Retrieve results
if model.status == GRB.OPTIMAL:
    for t in range(Tau):
        for s in range(S):
            print(f"Period {t}, Scenario {s}:")
            for g in range(G):
                print(f"  Generator {g}: Pg = {Pg[t, s, g].x}")
            print(f"  SoC = {SoC[t, s].x}")
