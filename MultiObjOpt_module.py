from pyomo.environ import *
import pandas as pd
def Run(df_prices, df_ghg, baseline_cost, baseline_ghg, LHV, RHO, freight_volume, fuel_consumption, max_cost_incrase, mode, mode_fuel_options):

    """
    Optimize the allocation of freight volume to different reporting fuels using Pyomo 
    to minimize the total fuel emissions of the freight sector, while keeping costs <20% increase relative to the baseline case.

    Args:
        df_prices (pd.DataFrame): The input fuel price data containing fuel costs for different scenarios.
        df_ghg (pd.DataFrame): The input fuel ghg emissions data containing emissions for different scenarios
        baseline_cost (pd.DataFrame): The baseline fuel cost used for comparison against reporting_fuel=petroleum diesel.
        baseline_ghg (pd.DataFrame): The baseline emissions for comparison against reporting_fuel=petroleum diesel
        LHV (dict): Lower heating values of fuels.
        RHO (dict): Density of fuels.
        freight_volume (dict): Freight volume split.
        fuel_consumption (dict): Fuel consumption profile (in G/mile).
        max_cost_increase : upper limit on total system cost increase
        mode (str): Transportation mode ("Highway", "Rail", "Maritime").
        mode_fuel_options (dict): which fuels to consider for allocation

    Returns:
        dict: A dictionary containing optimized allocations, emissions, and costs for each scenario.
    """
    # Filter the DataFrame for Year = 2050
    filtered_df_prices = df_prices[(df_prices['year'] == 2050)]
    filtered_df_ghg = df_ghg[(df_ghg['year'] == 2050)]

    # Initialize results dictionary
    results = {}

    #print(len(filtered_df_prices['scenario'].unique()))
    unique_scenarios = filtered_df_prices['scenario'].unique() # unique scenarios

    # Loop through each unique scenario in the filtered DataFrame
    for scenario in unique_scenarios:
        # Extract the rows corresponding to the current scenario
        # Remove Ammonia for Highway and Rail, remove different fuels for maritime
        def filter_fuels_prices(df, mode):
            selected_fuels = mode_fuel_options[mode]
            return df[df['reporting_fuel'].isin(selected_fuels)]
        
        def filter_fuels_ghg(df, mode):
            selected_fuels = mode_fuel_options[mode]
            return df[df['fuel'].isin(selected_fuels)]
        
        scenario_df_prices = filter_fuels_prices(filtered_df_prices[(filtered_df_prices['scenario'] == scenario)], mode)
        scenario_df_ghg = filter_fuels_ghg(filtered_df_ghg[(filtered_df_ghg['scenario'] == scenario)], mode)
        
        # if mode in ["Highway","Rail"]:
        #     scenario_df_prices = filtered_df_prices[(filtered_df_prices['scenario'] == scenario) & (~filtered_df_prices['reporting_fuel'].isin(['ammonia', 'electricity']))]
        #     scenario_df_ghg = filtered_df_ghg[(filtered_df_ghg['scenario'] == scenario) & (~filtered_df_ghg['fuel'].isin(['ammonia', 'electricity']))]
        # else:
        #     scenario_df_prices = filtered_df_prices[(filtered_df_prices['scenario'] == scenario) & (~filtered_df_prices['reporting_fuel'].isin(['e-diesel', 'electricity', 'FT biofuels', 'FT biofuels CCS', 'renewable diesel', 'hydrogen']))]
        #     scenario_df_ghg = filtered_df_ghg[(filtered_df_ghg['scenario'] == scenario) & (~filtered_df_ghg['fuel'].isin(['e-diesel', 'electricity', 'FT biofuels', 'FT biofuels CCS', 'renewable diesel', 'hydrogen']))]

        # Modify costs of FT biofuels and FT biofuels CCS for the Biomass Supply = Constrained case
        if scenario_df_prices['Biomass Supply'].iloc[1] in ["Constrained"] and mode in ["Highway", "Rail"]:
            scenario_df_prices.loc[scenario_df_prices['reporting_fuel'].isin(['FT biofuels', 'FT biofuels CCS']), 'price_USDperGJ'] = 2.5 * scenario_df_prices.loc[scenario_df_prices['reporting_fuel'].isin(['FT biofuels', 'FT biofuels CCS']), 'price_USDperGJ']
        
        # Sets: Reporting fuels
        reporting_fuels = scenario_df_prices['reporting_fuel'].to_list()
        
         # Define the optimization model
        model = ConcreteModel()
        model.fuels = Set(initialize=reporting_fuels) # set of fuels

        # Parameters: fuel costs and emissions
        gcam_fuel_costs = scenario_df_prices[['reporting_fuel','price_USDperGJ']]

        fuel_costs = {}
        for fuels in reporting_fuels:
            if mode=="Highway":
                fuel_costs[fuels] = gcam_fuel_costs[gcam_fuel_costs['reporting_fuel'] == fuels]['price_USDperGJ'].values * float(fuel_consumption['Highway'][fuels]) * (float(LHV['Highway'][fuels])/1000)*float(freight_volume['Highway'])
            elif mode=="Rail":
                fuel_costs[fuels] = gcam_fuel_costs[gcam_fuel_costs['reporting_fuel'] == fuels]['price_USDperGJ'].values * float(fuel_consumption['Rail'][fuels]) * (float(LHV['Rail'][fuels])/1000)*float(freight_volume['Rail'])
            elif mode=="Maritime":
                fuel_prices = gcam_fuel_costs[gcam_fuel_costs['reporting_fuel'] == fuels]['price_USDperGJ'].values * float(RHO['Maritime'][fuels]) * (float(LHV['Maritime'][fuels])/1000)
                fuel_costs[fuels] = 0.01*(2.636e-2 * fuel_prices + 8.841e-3 * 27.34 + 4.47e-6 * 287331 + 1.0411) * float(freight_volume['Maritime'])
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
                fuel_ghg[fuels] = fuel_ghg_df[fuels] * (float(LHV['Highway'][fuels])/1000) * float(fuel_consumption['Highway'][fuels]) * float(freight_volume['Highway']) #Million KgCO2eq
            elif mode=="Rail":
                fuel_ghg[fuels] = fuel_ghg_df[fuels] * (float(LHV['Rail'][fuels])/1000) * float(fuel_consumption['Rail'][fuels]) * float(freight_volume['Rail']) #Million KgCO2eq
            elif mode=="Maritime":
                fuel_ghg[fuels] = fuel_ghg_df[fuels] * (float(LHV['Maritime'][fuels])/1000) * (float(fuel_consumption['Maritime'][fuels])/1000) * float(freight_volume['Maritime']) #Million KgCO2eq
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
            return sum(model.cost[f] * model.allocation[f] for f in model.fuels) <= (1+ (max_cost_incrase/100))  * baseline_cost[scenario]
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

# end code