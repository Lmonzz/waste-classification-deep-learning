def get_category(predicted_label):
    if predicted_label == 'glass trash':
        return 'glass trash'
    elif predicted_label in ['batlua', 'daulocthuocla', 'thietbidientu']:
        return 'hazardous trash'
    elif predicted_label in ['book', 'cans', 'cardboard', 'milk_carton', 'paper', 'plastic_bottle']:
        return 'recyclables'
    elif predicted_label in ['khautrang', 'nylon', 'pen', 'pin']:
        return 'non-recycable trash'
    else:
        return 'unknown category'