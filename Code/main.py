import re
from genetic import eaSimpleWithElitism
from nurse import Nurse
from section_cover import SectionCover
from shift import Shift
from shift_request import ShiftRequest
from deap import base
from deap import creator
from deap import tools

import random

# problem constants:
HARD_CONSTRAINT_PENALTY = 100000  # the penalty factor for a hard-constraint violation

# Genetic Algorithm constants:
POPULATION_SIZE = 500
P_CROSSOVER = 0.8  # probability for crossover
P_MUTATION = 0.1   # probability for mutating an individual
MAX_GENERATIONS = 500
HALL_OF_FAME_SIZE = 100

# set the random seed:
RANDOM_SEED = 42


def parse_file(file_path):
    days = None
    shifts = []
    staff = []
    cover = []
    shifts_off = []
    shifts_on = []
    days_off_index = 0
    days_on_index = 0
    with open(file_path, 'r') as file:
        section = None
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("SECTION_"):
                section = re.split(r'_', line, maxsplit=1)[1]
                continue
            if section == "HORIZON":
                days = int(line)
            if section == "SHIFTS":
                parts = line.split(",")
                shift_id = parts[0]
                length = int(parts[1])
                cannot_follow = parts[2].split("|") if len(parts) > 2 else []
                shifts.append(Shift(shift_id, length, cannot_follow))
            if section == "STAFF":
                parts = line.split(",")
                name = parts[0]
                max_shifts = {part.split("=")[0] : part.split("=")[1]  for part in parts[1].split("|")}
                max_total_minutes = int(parts[2])
                min_total_minutes = int(parts[3])
                max_consecutive_shifts = int(parts[4])
                min_consecutive_shifts = int(parts[5])
                min_consecutive_days_off = int(parts[6])
                max_weekends = int(parts[7])
                staff.append(Nurse(name=name, max_shifts=max_shifts, max_total_minutes=max_total_minutes, min_total_minutes=min_total_minutes, max_consecutive_shifts=max_consecutive_shifts, min_consecutive_shifts=min_consecutive_shifts, min_consecutive_days_off=min_consecutive_days_off, max_weekends=max_weekends))
            if section == "DAYS_OFF":
                parts = line.split(",")
                nurse = next((nurse for nurse in staff if nurse.name == parts[0]), None)
                nurse.days_off = parts[1:]
                days_off_index +=1
            if section == "SHIFT_ON_REQUESTS":
                parts = line.split(",")
                nurse = parts[0]
                day = int(parts[1])
                shift_name = parts[2]
                weight = int(parts[3])
                shifts_on.append(ShiftRequest(nurse=nurse, day=day,shift_name=shift_name,weight=weight))
            if section == "SHIFT_OFF_REQUESTS":
                parts = line.split(",")
                nurse = parts[0]
                day = int(parts[1])
                shift_name = parts[2]
                weight = int(parts[3])
                shifts_off.append(ShiftRequest(nurse=nurse, day=day,shift_name=shift_name,weight=weight))
            if section == "COVER":
                parts = line.split(",")
                day = int(parts[0])
                shift_name = parts[1]
                requirement = int(parts[2])
                weight_for_under = int(parts[3])
                weight_for_over = int(parts[4])
                cover.append(SectionCover(day=day, shift_name=shift_name, requirement=requirement, weight_for_under=weight_for_under, weight_for_over=weight_for_over))
            
    return days, shifts, staff, cover, shifts_off, shifts_on

days, shifts, staff, cover, shifts_off, shifts_on = parse_file("instance.txt")


def create_individual(values, days):
    nurse_schedule = []
    for _ in range(0, days):
        nurse_schedule += [random.choice(values)]
    return nurse_schedule
        
def get_shifts(shifts):
    shift_names =  [shift.name for shift in shifts]
    shift_names += ['free']
    return shift_names

def hard_constraint_calculate_shifts_following_current_shift(schedule):
    number_of_constrains = 0
    for nurse_schedule in schedule:
        for i in range(0, len(nurse_schedule)-1):
            if nurse_schedule[i] != 'free' and nurse_schedule[i+1] != 'free':
                #first constraint
                shift = next((shift for shift in shifts if shift.name == nurse_schedule[i]), None)
                if nurse_schedule[i+1] in shift.restricted_shifts:
                    number_of_constrains +=1
    return number_of_constrains

def hard_constraint_2(schedule):
    number_of_constrains = 0
    index = 0
    for nurse_schedule in schedule:
        
        nurse = staff[index]
        
        #dict for seeing how many items of each type are in every nurse schedule
        number_of_shifts = {}
        #variable for checking each nurse worked time based on shift type
        total_minutes = 0
        #variables for checking the maximum and minimum number off consecutive shifts
        max_continous_working_days = 0
        min_continous_working_days = 1000000
        current_continous_working_days = 0
        #minimum consecutive days off
        current_days_off = 0
        min_days_off = 1000000
        
        
        week_added = False
        total_weeks_worked = 0
        
        days_off_worked = 0
        
        for i, shift_type in enumerate(nurse_schedule):
            if shift_type in number_of_shifts:
                number_of_shifts[shift_type] +=1
            else:
                number_of_shifts[shift_type] = 1
        
            if(shift_type != 'free'):
                #total minutes calculation
                shift = next((shift for shift in shifts if shift.name == shift_type), None)
                total_minutes += shift.length
                
                current_continous_working_days += 1
                
                if current_days_off < min_days_off:
                    min_days_off = current_days_off
            
                current_days_off = 0
               
            else:    
                
                if current_continous_working_days > max_continous_working_days:
                    max_continous_working_days = current_continous_working_days
                
                if current_continous_working_days < min_continous_working_days:
                    min_continous_working_days = current_continous_working_days
                
                current_continous_working_days = 0
                
                current_days_off += 1
            
            if i%7 == 0:
                week_added = False
                
            if i%7 == 5 or i%7 == 6:
                if shift_type != 'free' and week_added == False:
                    total_weeks_worked += 1
                    week_added = True
                    
            
            #days off
            
        for day_off in nurse.days_off:
            if nurse_schedule[int(day_off)] != 'free':
                days_off_worked +=1
                    
            
        for max_shift_key, max_shift_value in nurse.max_shifts.items():
            if max_shift_key in number_of_shifts and number_of_shifts[max_shift_key] > int(max_shift_value):
                number_of_constrains +=1
                
        if total_minutes > nurse.max_total_minutes:
            number_of_constrains += 1
            
        if total_minutes < nurse.min_total_minutes:
            number_of_constrains += 1
            
        if max_continous_working_days > nurse.max_consecutive_shifts:
            number_of_constrains += 1
            
        if min_continous_working_days > nurse.min_consecutive_shifts:
            number_of_constrains += 1 
            
        if total_weeks_worked > nurse.max_weekends:
            number_of_constrains += 1
            
        if days_off_worked != 0:
            number_of_constrains += 1
            
        index+=1
        
    return number_of_constrains    
       

def soft_constrains(schedule):
    
    total_soft_constrains_cost = 0
    
    nurse_schedule_dict = {}

    for i, nurse in enumerate(staff):
        nurse_schedule_dict[nurse.name] = schedule[i]
    
    for shift_off in shifts_off:
        nurse_schedule = nurse_schedule_dict.get(shift_off.nurse)
        if nurse_schedule[shift_off.day] == shift_off.shift_name:
                total_soft_constrains_cost += shift_off.weight
                
    for shift_on in shifts_on:
        nurse_schedule = nurse_schedule_dict.get(shift_on.nurse)
        if nurse_schedule[shift_on.day] != shift_on.shift_name:
                total_soft_constrains_cost += shift_on.weight
    
        
    for individual_cover in cover:
        
        current_day_schedule = [row[individual_cover.day] for row in schedule]
        
        number_of_shifts = current_day_schedule.count(individual_cover.shift_name)
        
        if number_of_shifts < individual_cover.requirement:
            total_soft_constrains_cost += (individual_cover.requirement - number_of_shifts) * individual_cover.weight_for_under
            
        elif number_of_shifts > individual_cover.requirement:
            total_soft_constrains_cost += (number_of_shifts - individual_cover.requirement) * individual_cover.weight_for_over
            
    return total_soft_constrains_cost    
        

def calculate_cost(schedule):
    total_number_of_hard_constrains = 0
    total_number_of_soft_constrains = 0
    
    total_number_of_hard_constrains += hard_constraint_calculate_shifts_following_current_shift(schedule)
    total_number_of_hard_constrains += hard_constraint_2(schedule)
    
    total_number_of_soft_constrains = soft_constrains(schedule)
    
    return total_number_of_soft_constrains + total_number_of_hard_constrains * HARD_CONSTRAINT_PENALTY,

def calculate_cost_2(schedule):
    total_number_of_hard_constrains = 0
    total_number_of_soft_constrains = 0
    
    total_number_of_hard_constrains += hard_constraint_calculate_shifts_following_current_shift(schedule)
    total_number_of_hard_constrains += hard_constraint_2(schedule)
    
    print(total_number_of_hard_constrains)
    print(total_number_of_soft_constrains)
    
    total_number_of_soft_constrains = soft_constrains(schedule)
    
    return total_number_of_soft_constrains + total_number_of_hard_constrains * HARD_CONSTRAINT_PENALTY,

tournsize=1
def mutate_custom(individual, values, indpb):
    for element in individual:
        for i in range(0,len(element)):
            if random.random() < indpb:
                element[i] = random.choice(values)
                
    return individual,

def init_algoritm(values, days, number_of_nurses):
    
    random.seed(RANDOM_SEED)
    
    toolbox = base.Toolbox()
    
    # define a single objective, maximizing fitness strategy:
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))

    # create the Individual class based on list:
    creator.create("Individual", list, fitness=creator.FitnessMin)
    
    toolbox.register("ShiftForNurse", create_individual, values, days)    
    
    # create the individual operator to fill up an Individual instance:
    toolbox.register("IndividualCreator", tools.initRepeat, creator.Individual, toolbox.ShiftForNurse, number_of_nurses)

    # create the population operator to generate a list of individuals:
    toolbox.register("populationCreator", tools.initRepeat, list, toolbox.IndividualCreator)
    
    toolbox.register("evaluate", calculate_cost)

    # genetic operators:
    toolbox.register("select", tools.selTournament, tournsize=tournsize)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", mutate_custom, values=values, indpb=P_MUTATION)

    return toolbox
    
    
    
def main():
    
    shifts_names = get_shifts(shifts)
        
    toolbox = init_algoritm(shifts_names, days, len(staff))
    
    population = toolbox.populationCreator(POPULATION_SIZE)
    
    hof = tools.HallOfFame(HALL_OF_FAME_SIZE)

    # perform the Genetic Algorithm flow with hof feature added:
    eaSimpleWithElitism(population, toolbox, cxpb=P_CROSSOVER, mutpb=P_MUTATION,
                                               ngen=MAX_GENERATIONS, halloffame=hof)
    
    best = hof.items[0]
    print("Best Individual:", best)
    print()
    print("Best Fitness:", best.fitness.values[0])
    
    calculate_cost_2(best)
    

if __name__ == "__main__":
    main()