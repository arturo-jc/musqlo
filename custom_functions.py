def most_exercises_in_layer(layer):
    result = 0
    for element in layer:
        if isinstance(element, Workout):
            if len(element.exercises) > result:
                result = len(element.exercises)
    return result
