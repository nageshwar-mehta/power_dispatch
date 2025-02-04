import numpy as np
from power_dispatch1_0 import model, Tau, S, G, Pg, Pw, Pz, SoC
from gurobipy import GRB

#
import matplotlib.pyplot as plt

# Visualization function
def plot_results(Tau, S, G, Pg, Pw, Pz, SoC):
    # Initialize arrays for plotting
    total_generation = np.zeros((Tau, S))
    wind_used = np.zeros((Tau, S))
    load_shedding = np.zeros((Tau, S))
    soc = np.zeros((Tau, S))

    # Extract results
    for t in range(Tau):
        for s in range(S):
            total_generation[t, s] = sum(Pg[t, s, g].x for g in range(G))
            wind_used[t, s] = Pw[t, s].x
            load_shedding[t, s] = Pz[t, s].x
            soc[t, s] = SoC[t, s].x

    # Plot total generation and wind usage
    plt.figure(figsize=(10, 6))
    for s in range(S):
        plt.plot(range(Tau), total_generation[:, s], label=f"Scenario {s}: Total Gen", linestyle='--')
        plt.plot(range(Tau), wind_used[:, s], label=f"Scenario {s}: Wind Used")
    plt.title("Total Generation vs. Wind Power Utilization")
    plt.xlabel("Dispatch Period")
    plt.ylabel("Power (MW)")
    plt.legend()
    plt.grid()
    plt.show()

    # Plot state of charge (SoC)
    plt.figure(figsize=(10, 6))
    for s in range(S):
        plt.plot(range(Tau), soc[:, s], label=f"Scenario {s}")
    plt.title("Battery State of Charge (SoC) Over Time")
    plt.xlabel("Dispatch Period")
    plt.ylabel("State of Charge (MW)")
    plt.legend()
    plt.grid()
    plt.show()

    # Plot load shedding
    plt.figure(figsize=(10, 6))
    for s in range(S):
        plt.bar(range(Tau), load_shedding[:, s], label=f"Scenario {s}")
    plt.title("Load Shedding Over Time")
    plt.xlabel("Dispatch Period")
    plt.ylabel("Load Shedding (MW)")
    plt.legend()
    plt.grid()
    plt.show()

# Call the visualization function after optimization
if model.status == GRB.OPTIMAL:
    plot_results(Tau, S, G, Pg, Pw, Pz, SoC)