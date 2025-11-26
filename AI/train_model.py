# ========================================
# train_model.py
# ========================================
# Script traint een neuraal netwerk om planten te herkennen
# op basis van eerder geaugmenteerde afbeeldingen.
# Gebruikt een pretrained ResNet18 (ImageNet1K_V1).
# Alleen de laatste laag wordt aangepast voor de plantklassen.
# ========================================

import os
import torch
from torchvision import datasets, models, transforms
from torch import nn, optim
from torch.utils.data import DataLoader

# -------------------------
# 1. Basisinstellingen
# -------------------------

data_dir = "augmented_dataset"      # Map met geaugmenteerde afbeeldingen per plantsoort
model_save_path = "plant_model.pth" # Naam van het bestand waarin het getrainde model wordt opgeslagen
batch_size = 16                     # Aantal afbeeldingen per batch (kleine dataset = lage waarde)
num_epochs = 12                      # Aantal herhalingen over het volledige dataset (kan lager op laptop bijvoorbeeld)
learning_rate = 0.001               # Snelheid waarmee het model leert

# Controleert of een GPU beschikbaar is,
#
# indien niet, wordt CPU gebruikt
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("✅ Training wordt uitgevoerd op:", device)

# -------------------------
# 2. Data loading en preprocessing
# -------------------------
# De DataLoader leest afbeeldingen uit de datasetfolders.
# Elke submap (bijv. plant_1, plant_2) wordt automatisch als een aparte klasse gezien.
# De transform zorgt ervoor dat alle afbeeldingen op dezelfde manier worden voorbereid.

train_transforms = transforms.Compose([
    transforms.Resize((224, 224)),  # Schaal elke afbeelding naar 224x224 pixels (standaard inputformaat ResNet)
    transforms.ToTensor(),          # Zet afbeelding om naar tensor (nodig voor PyTorch)
])

# Laadt de dataset met bovenstaande transformaties
train_dataset = datasets.ImageFolder(data_dir, transform=train_transforms)

# Maakt batches van afbeeldingen die door het model worden gebruikt tijdens training
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

# Bepaalt automatisch het aantal plantsoorten (klassen)
num_classes = len(train_dataset.classes)
print("🌱 Aantal plantsoorten gevonden:", num_classes)
print("Klassenlabels:", train_dataset.classes)

# -------------------------
# 3. Model laden (ResNet18)
# -------------------------
# ResNet18 is een veelgebruikt convolutioneel neuraal netwerk voor beeldherkenning.
# Er wordt een versie gebruikt die al getraind is op ImageNet (1000 objectcategorieën).
# Alle lagen worden ‘gefreezed’ behalve de laatste, zodat enkel de eindlaag wordt getraind
# voor herkenning van de eigen plantsoorten (transfer learning).

model = models.resnet18(weights="IMAGENET1K_V1")  # Laadt pretrained model
for param in model.parameters():
    param.requires_grad = False  # Alle bestaande lagen niet aanpassen tijdens training

# De laatste laag vervangen door een nieuwe die past bij het aantal plantklassen
model.fc = nn.Linear(model.fc.in_features, num_classes)
model = model.to(device)  # Model verplaatsen naar GPU of CPU

# -------------------------
# 4. Loss functie en optimizer
# -------------------------
# De loss functie berekent het verschil tussen de voorspelling en het echte label.
# De optimizer bepaalt hoe de gewichten van het model worden aangepast op basis van de loss.

criterion = nn.CrossEntropyLoss()             # Standaard loss functie voor classificatie
optimizer = optim.Adam(model.fc.parameters(), lr=learning_rate)  # Alleen de nieuwe laag trainen

# -------------------------
# 5. Training loop
# -------------------------
# Het model wordt meerdere keren (epochs) over de dataset getraind.
# Na elke batch wordt de loss berekend, de fout teruggevoerd (backpropagation),
# en de gewichten aangepast. Accuraatheid wordt berekend als controle op voortgang.

print("🚀 Start training...")
for epoch in range(num_epochs):
    running_loss = 0.0   # Totaal van de loss binnen dit epoch
    correct = 0          # Aantal correcte voorspellingen
    total = 0            # Totaal aantal voorspellingen

    # Doorloopt alle batches in de dataset
    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)  # Data naar GPU/CPU verplaatsen

        optimizer.zero_grad()       # Gradients resetten (anders stapelt de fout zich op)
        outputs = model(images)     # Model maakt voorspellingen voor de batch
        loss = criterion(outputs, labels)  # Bereken verschil tussen voorspelling en werkelijkheid
        loss.backward()             # Backpropagation: fout terugsturen door het netwerk
        optimizer.step()            # Modelgewichten aanpassen

        running_loss += loss.item()  # Loss optellen voor gemiddelde berekening
        _, predicted = torch.max(outputs, 1)  # Klasse met hoogste waarschijnlijkheid selecteren
        total += labels.size(0)               # Totaal aantal afbeeldingen in batch bijhouden
        correct += (predicted == labels).sum().item()  # Tellen hoeveel voorspellingen juist zijn

    # Gemiddelde resultaten na elk epoch tonen
    accuracy = 100 * correct / total
    avg_loss = running_loss / len(train_loader)
    print(f"Epoch [{epoch+1}/{num_epochs}] | Loss: {avg_loss:.4f} | Acc: {accuracy:.2f}%")

# -------------------------
# 6. Model opslaan
# -------------------------
# Na de training worden de gewichten van het model opgeslagen in een .pth-bestand.
# Dit bestand kan later geladen worden in een testscript om nieuwe afbeeldingen te classificeren.

torch.save(model.state_dict(), model_save_path)
print(f"✅ Training voltooid. Model opgeslagen als '{model_save_path}'")
