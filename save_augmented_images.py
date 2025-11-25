import os, random
from PIL import Image
from torchvision import transforms
from tqdm import tqdm

# ===============================
# 1. Configuratie
# ===============================
source_dir = "."           # Map waar de originele plant_x folders staan
augmented_dir = "augmented_dataset"  # Map waar de nieuwe (augmented) foto's worden opgeslagen
test_dir = "test_set"      # Map voor test data (klein deel van de dataset)
num_augments = 20          # Hoeveel nieuwe (aangepaste) foto's per originele foto
test_split = 0.2           # Percentage dat naar de test set gaat (20%)

# ===============================
# 2. Augmentation pipeline
# ===============================
# Hier definiëren we welke bewerkingen (filters) op de foto's worden toegepast.
augment = transforms.Compose([
    transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),       # Willekeurig uitsnijden en schalen
    transforms.RandomHorizontalFlip(),                         # Spiegeling horizontaal
    transforms.RandomVerticalFlip(),                           # Spiegeling verticaal
    transforms.RandomRotation(40),                             # Willekeurige rotatie (tot 40 graden)
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3, hue=0.1),  # Kleurvariaties
    transforms.GaussianBlur(kernel_size=(3, 3)),                # Beetje vervaging toevoegen
])

# ===============================
# 3. Maak output mappen aan
# ===============================
# Zorgt dat de output folders bestaan (maakt ze aan als ze niet bestaan)
for d in [augmented_dir, test_dir]:
    os.makedirs(d, exist_ok=True)

# ===============================
# 4. Loop door alle planten
# ===============================
for plant_folder in os.listdir(source_dir):
    path = os.path.join(source_dir, plant_folder)
    if not os.path.isdir(path) or not plant_folder.startswith("plant_"):
        continue  # sla over als het geen plant_x map is

    # Mappen voor deze specifieke plant aanmaken
    aug_save = os.path.join(augmented_dir, plant_folder)
    test_save = os.path.join(test_dir, plant_folder)
    os.makedirs(aug_save, exist_ok=True)
    os.makedirs(test_save, exist_ok=True)

    # Doorloop alle afbeeldingen in de map
    for img_name in tqdm(os.listdir(path), desc=f"Processing {plant_folder}"):
        if not img_name.lower().endswith((".jpg", ".jpeg", ".png")):
            continue  # sla niet-afbeeldingen over

        image = Image.open(os.path.join(path, img_name)).convert("RGB")

        # Maak meerdere versies (augmentations) van elke originele afbeelding
        for i in range(num_augments):
            aug_img = augment(image)

            # Willekeurig deel (20%) naar test set, rest naar training set
            save_folder = test_save if random.random() < test_split else aug_save

            # Bestandsnaam aanpassen met "_aug_x"
            out_name = f"{os.path.splitext(img_name)[0]}_aug_{i+1}.jpg"
            aug_img.save(os.path.join(save_folder, out_name))

print("✅ Augmentation klaar! Nieuwe data opgeslagen in 'augmented_dataset/' en 'test_set/'")
