import pandas as pd
from pyomo.environ import *

import BaselineObj

# Load the CSV prices file into a DataFrame
file_path = 'Data/public.task_4.fuels_prices.csv' 
df_prices = pd.read_csv(file_path)

# Load the CSV emissions file into a DataFrame
file_path = 'Data/public.task_4.fuels_lca_ghg.csv' 
df_ghg = pd.read_csv(file_path)

# Total freight volume 2050 (Billion ton-miles)
freight_volume = {
    "Highway": 926.43318,
    "Rail": 604.510158,
    "Maritime": 220.998
}
fuel_consumption = {
    "petroleum diesel": {
        "Highway": 20,
        "Rail": 6,
        "Maritime": 14,
    },
    "e-diesel": {
        "Highway": 20,
        "Rail": 6,
    },
    "FT biofuels": {
        "Highway": 20,
        "Rail": 6,
    },
    "FT biofuels CCS": {
        "Highway": 20,
        "Rail": 6,
    },
    "renewable diesel": {
        "Highway": 20,
        "Rail": 6,
    },
    "ammonia": {
        "Maritime": 35,
    },
    "hydrogen": {
        "Highway": 8,
        "Rail": 1.8,
        "Maritime": 6,
    },
    "LNG": {
        "Highway": 24,
        "Rail": 5,
        "Maritime": 12,
    },
    "electricity": {
        "Highway": 3.6,
        "Rail": 3.6,
    }
}

# Fuel inputs (LHV MJ/Kg and Rho Kg/gallon: i.e., density)
LHV = {
    "petroleum diesel": {
        "Highway": 42.8,
        "Rail": 42.8,
        "Maritime": 42.8,
    },
    "e-diesel": {
        "Rail": 42.8,
        "Highway": 42.8,
    },
    "renewable diesel": {
        "Rail": 42.8,
        "Highway": 42.8,
    },
    "FT biofuels": {
        "Rail": 42.8,
        "Highway": 42.8,
    },
    "FT biofuels CCS": {
        "Rail": 42.8,
        "Highway": 42.8,
    },
    "ammonia": {
        "Maritime": 18.6,
    },
    "hydrogen": {
        "Highway": 120,
        "Rail": 120,
        "Maritime": 120,
    },
    "LNG": {
        "Highway": 45,
        "Rail": 45,
        "Maritime": 45,
    },
    "electricity": {
        "Highway": 0.125,
        "Rail": 0.03,
    },
}
RHO = {
    "petroleum diesel": {
        "Highway": 3.25,
        "Rail": 3.25,
        "Maritime": 3.25,
    },
    "e-diesel": {
        "Rail": 3.25,
        "Highway": 3.25,
    },
    "renewable diesel": {
        "Rail": 3.25,
        "Highway": 3.25,
    },
    "FT biofuels": {
        "Rail": 3.25,
        "Highway": 3.25,
    },
    "FT biofuels CCS": {
        "Rail": 3.25,
        "Highway": 3.25,
    },
    "ammonia": {
        "Maritime": 2.58,
    },
    "hydrogen": {
        "Highway": 0.268,
        "Rail": 0.268,
        "Maritime": 0.268,
    },
    "LNG": {
        "Highway": 1.89,
        "Rail": 1.89,
        "Maritime": 1.89,
    },
}
# Calculate prices and emissions for the baseline 2050 case (fuel=petroleum diesel)
BaselineOutputs = BaselineObj.Run(df_prices, df_ghg, LHV, RHO, freight_volume)

(highway_base_prices, rail_base_prices, maritime_base_prices, highway_base_ghg, rail_base_ghg, maritime_base_ghg) = BaselineOutputs

# Display the extracted baseline prices grouped by scenario for highway
for scenario, prices in highway_base_prices.items():
    print(f"Scenario: {scenario}, Highway_Prices: {prices}")

# Display the extracted baseline prices grouped by scenario for Rail
for scenario, prices in rail_base_prices.items():
    print(f"Scenario: {scenario}, Rail_Prices: {prices}")

# Display the extracted baseline prices grouped by scenario for Maritime
for scenario, prices in maritime_base_prices.items():
    print(f"Scenario: {scenario}, Maritime_Prices: {prices}")

# Display the extracted baseline emissions grouped by scenario for highway
for scenario, ghg in highway_base_ghg.items():
    print(f"Scenario: {scenario}, Highway_GHG: {ghg}")

# Display the extracted baseline emissions grouped by scenario for Rail
for scenario, ghg in rail_base_ghg.items():
    print(f"Scenario: {scenario}, Rail_GHG: {ghg}")

# Display the extracted baseline emissions grouped by scenario for Maritime
for scenario, ghg in maritime_base_ghg.items():
    print(f"Scenario: {scenario}, Maritime_GHG: {ghg}")


def optimize_fuel_allocation(dframe_prices, dframe_ghg, baseline_cost, baseline_ghg, LHV, RHO, freight_volume, fuel_consumption, mode):
    """
    Optimize the allocation of freight volume to different reporting fuels using Pyomo 
    to minimize the total fuel emissions of the freight sector, while keeping costs <20% increase relative to the baseline case.

    Args:
        dframe_prices (pd.DataFrame): The input fuel price data containing fuel costs for different scenarios.
        dframe_ghg (pd.DataFrame): The input fuel ghg emissions data containing emissions for different scenarios
        baseline_cost (pd.DataFrame): The baseline fuel cost used for comparison against reporting_fuel=petroleum diesel.
        baseline_ghg (pd.DataFrame): The baseline emissions for comparison against reporting_fuel=petroleum diesel

    Returns:
        dict: A dictionary containing optimized allocations, emissions, and costs for each scenario.
    """
    # Filter the DataFrame for Year = 2050
    filtered_df_prices = dframe_prices[(dframe_prices['year'] == 2050)]
    filtered_df_ghg = dframe_ghg[(dframe_ghg['year'] == 2050)]

    # Initialize results dictionary
    results = {}

    print(len(filtered_df_prices['scenario'].unique()))
    unique_scenarios = filtered_df_prices['scenario'].unique() # unique scenarios

    # Loop through each unique scenario in the filtered DataFrame
    for scenario in unique_scenarios:
        # Extract the rows corresponding to the current scenario
        # Remove Ammonia for Highway and Rail, remove different fuels for maritime
        if mode == "Highway" or mode == "Rail":
            scenario_df_prices = filtered_df_prices[(filtered_df_prices['scenario'] == scenario) & (~filtered_df_prices['reporting_fuel'].isin(['ammonia', 'electricity']))]
            scenario_df_ghg = filtered_df_ghg[(filtered_df_ghg['scenario'] == scenario) & (~filtered_df_ghg['fuel'].isin(['ammonia', 'electricity']))]
        else:
            scenario_df_prices = filtered_df_prices[(filtered_df_prices['scenario'] == scenario) & (~filtered_df_prices['reporting_fuel'].isin(['e-diesel', 'electricity', 'FT biofuels', 'FT biofuels CCS', 'renewable diesel']))]
            scenario_df_ghg = filtered_df_ghg[(filtered_df_ghg['scenario'] == scenario) & (~filtered_df_ghg['fuel'].isin(['e-diesel', 'electricity', 'FT biofuels', 'FT biofuels CCS', 'renewable diesel']))]

        # Define the optimization model
        model = ConcreteModel()

        # Sets: Reporting fuels
        reporting_fuels = scenario_df_prices['reporting_fuel'].to_list()
        
        model.fuels = Set(initialize=reporting_fuels)

        # Parameters: fuel costs and ghg emissions
        gcam_fuel_costs = scenario_df_prices[['reporting_fuel','price_USDperGJ']]
        fuel_costs = {}
        for fuels in reporting_fuels:
            if mode=="Highway":
                fuel_costs[fuels] = gcam_fuel_costs[gcam_fuel_costs['reporting_fuel'] == fuels]['price_USDperGJ'].values * RHO[fuels]['Highway'] * (LHV[fuels]['Highway']/1000)*2.636e-2*freight_volume['Highway']
            elif mode=="Rail":
                fuel_costs[fuels] = gcam_fuel_costs[gcam_fuel_costs['reporting_fuel'] == fuels]['price_USDperGJ'].values * RHO[fuels]['Rail'] * (LHV[fuels]['Rail']/1000)*2.636e-2*freight_volume['Rail']
            elif mode=="Maritime":
                fuel_prices = gcam_fuel_costs[gcam_fuel_costs['reporting_fuel'] == fuels]['price_USDperGJ'].values * RHO[fuels]['Maritime'] * (LHV[fuels]['Maritime']/1000)
                fuel_costs[fuels] = 0.01*(2.636e-2 * fuel_prices + 8.841e-3 * 27.34 + 4.47e-6 * 287331 + 1.0411) * freight_volume['Maritime']
            else:
                print(f"Fuel cost allocation failed for scenario: {scenario}")
            
        model.cost = Param(model.fuels, initialize=dict(zip(reporting_fuels, fuel_costs.values())))
        fuel_ghg_df = {}
        for fuels in reporting_fuels:
            fuel_ghg_df[fuels] = scenario_df_ghg[scenario_df_ghg['fuel'] == fuels]['kgCO2e_GJ'].sum()

        #gcam_fuel_ghg = list(fuel_ghg_df.values())
        fuel_ghg = {}
        for fuels in reporting_fuels:
            if mode=="Highway":
                fuel_ghg[fuels] = fuel_ghg_df[fuels] * (LHV[fuels]['Highway']/1000) * fuel_consumption[fuels]['Highway'] * freight_volume['Highway'] #Million KgCO2eq
            elif mode=="Rail":
                fuel_ghg[fuels] = fuel_ghg_df[fuels] * (LHV[fuels]['Rail']/1000) * fuel_consumption[fuels]['Rail'] * freight_volume['Rail'] #Million KgCO2eq
            elif mode=="Maritime":
                fuel_ghg[fuels] = fuel_ghg_df[fuels] * (LHV[fuels]['Maritime']/1000) * fuel_consumption[fuels]['Maritime'] * freight_volume['Maritime'] #Million KgCO2eq
            else:
                print(f"Fuel ghg allocation failed for scenario: {scenario}")

        model.ghg = Param(model.fuels, initialize=dict(zip(reporting_fuels, fuel_ghg.values())))   
    
        # Variables: Fraction of freight volume allocated to each fuel
        model.allocation = Var(model.fuels, bounds=(0,1))

        # Objective: Minimize relative total fuel ghg
        def objective_rule(model):
            return sum(model.ghg[f] * model.allocation[f] for f in model.fuels)
        model.objective = Objective(rule=objective_rule, sense=minimize)

        # Constraint: Total allocation must sum to 100% of freight volume
        def total_allocation_constraint(model):
            return sum(model.allocation[f] for f in model.fuels) ==1
        model.total_allocation = Constraint(rule=total_allocation_constraint)

        # Constraint: Total cost increase < 20% from baseline cost of diesel
        def total_cost_increase(model):
            return sum(model.cost[f] * model.allocation[f] for f in model.fuels) <= 1 * baseline_cost[scenario]
        model.cost_increase = Constraint(rule=total_cost_increase)

        # Solve the optimization problem
        solver = SolverFactory('glpk') # Use GLPK solver; replace with 'gurobi' if available
        result = solver.solve(model)

        if result.solver.status == SolverStatus.ok and result.solver.termination_condition == TerminationCondition.optimal:
            # Extract optimized allocations
            print(f"Optimization succeded for scenario: {scenario}")
            allocations = {f: model.allocation[f].value for f in reporting_fuels}
            minimized_ghg = model.objective()
            total_cost = sum(model.allocation[f].value * model.cost[f] for f in reporting_fuels)

            # Store results
            results[scenario] = {
                "allocations": allocations,
                "percent_ghg": ((minimized_ghg/baseline_ghg[scenario])-1)*100, # convert to percentage change
                "percent_cost": ((total_cost/baseline_cost[scenario])-1)*100 # convert to percentage change
            }
        else:
            print(f"Optimization failed for scenario: {scenario}")
            results[scenario] = {"allocations": None, "percent_ghg": None, "percent_cost": None}
    
    return results

# Function to nicely print the optimization results
def print_optimized_results(output_dict, mode):
    """
    Prints optimized fuel allocations, percent GHG, and percent cost for each scenario.
    
    Args:
        output_dict (dict): Dictionary containing optimization results.
        mode (str): Mode of transportation (e.g., 'Highway', 'Rail', 'Maritime').
    """
    print(f"\nOptimization Results for {mode}:")
    print("=" * 50)
    for scenario, result in output_dict.items():
        print(f"Scenario: {scenario}")
        if result["allocations"] is not None:
            print(f"  Fuel Allocations: {result['allocations']}")
            print(f"  Percent GHG Change: {result['percent_ghg']:.2f}")
            print(f"  Percent Cost Change: {float(result['percent_cost'][0]):.2f}")
        else:
            print("  Optimization failed for this scenario.")
        print("-" * 50)


# Optimize fuel deployment for highway (year 2050)
highway_outputs = optimize_fuel_allocation(df_prices, df_ghg, highway_base_prices, highway_base_ghg, LHV, RHO, freight_volume, fuel_consumption, "Highway")
#Highway fuel options: (a) e-diesel (b) electricity (c) FT biofuels (d) FT biofuels CCS (e) hydrogen (f) LNG (g) Diesel (h) renewable diesel

#Optimize fuel deployment for Rail (year 2050)
rail_outputs = optimize_fuel_allocation(df_prices, df_ghg, rail_base_prices, rail_base_ghg, LHV, RHO, freight_volume, fuel_consumption, "Rail")
#Rail fuel options: (a) e-diesel (b) electricity (c) FT biofuels (d) FT biofuels CCS (e) hydrogen (f) LNG (g) Diesel (h) renewable diesel

# Optimize fuel deployment for Maritime (year 2050)
maritime_outputs = optimize_fuel_allocation(df_prices, df_ghg, maritime_base_prices, maritime_base_ghg, LHV, RHO, freight_volume, fuel_consumption, "Maritime")
# Maritime fuel options: Hydrogen (f) LNG (g) Diesel (h) Ammonia

# Print results for Highway optimization
print_optimized_results(highway_outputs, "Highway")

# Print results for Rail optimization
print_optimized_results(rail_outputs, "Rail")

# Print results for Maritime optimization
print_optimized_results(maritime_outputs, "Maritime")