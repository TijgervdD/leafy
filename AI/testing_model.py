# ==========================================
# test_model.py
# ==========================================
# - Kan één afbeelding of de volledige test_set testen
# - Toont voorspellingen per afbeelding
# - Berekent nauwkeurigheid (accuracy)
# - Schrijft misclassificaties naar CSV
# - Maakt een confusion matrix als PNG
# ==========================================

import os
import csv
import torch
from torchvision import models, transforms
from PIL import Image
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
import numpy as np

# ==========================================
# Basisinstellingen
# ==========================================

model_path = "plant_model.pth"  # pad naar het getrainde model
test_dir = "test_set"  # map met testafbeeldingen
output_csv = "test_misclassifications.csv"  # bestand waarin fouten worden opgeslagen
confusion_png = "confusion_matrix.png"  # uitvoerbestand voor de confusion matrix
single_image_path = None  # voorbeeld: "test_set/plant_2/example.jpg" → test één afbeelding

# ==========================================
# Klassen en model laden
# ==========================================

class_names = sorted([d for d in os.listdir(test_dir) if os.path.isdir(os.path.join(test_dir, d))])  # haalt de mappen/klassen op
num_classes = len(class_names)  # aantal plantsoorten
print(f"Gevonden plantklassen: {class_names}")

model = models.resnet18(weights=None)  # zelfde model als bij training
model.fc = torch.nn.Linear(model.fc.in_features, num_classes)  # outputlaag aanpassen aan aantal klassen
model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))  # modelgewichten laden
model.eval()  # model in evaluatiemodus zetten

# ==========================================
# Transformaties
# ==========================================

transform = transforms.Compose([
    transforms.Resize((224, 224)),  # formaat consistent houden
    transforms.ToTensor(),  # omzetten naar tensor
])

# ==========================================
# Functie voor één afbeelding
# ==========================================

def predict_image(image_path):
    image = Image.open(image_path).convert("RGB")  # afbeelding openen en converteren naar RGB
    img_t = transform(image).unsqueeze(0)  # transformaties toepassen en batchdimensie toevoegen

    with torch.no_grad():  # geen gradienten nodig tijdens inferentie
        outputs = model(img_t)  # modelvoorspelling
        _, pred_idx = torch.max(outputs, 1)  # index met hoogste score nemen

    predicted_label = class_names[pred_idx.item()]  # label opzoeken
    print(f"📷 {os.path.basename(image_path)} → Herkend als: {predicted_label}")  # print resultaat
    return predicted_label, pred_idx.item()  # label + index teruggeven

# ==========================================
# Testmodus
# ==========================================

if single_image_path:  # test één afbeelding
    label, _ = predict_image(single_image_path)  # voorspelling uitvoeren
    print(f"\n✅ Voorspelling voltooid: {label}")  # resultaat tonen

else:  # test volledige dataset
    y_true, y_pred = [], []  # echte labels en voorspellingen
    misclassified = []  # lijst voor fouten
    total, correct = 0, 0  # counters

    for idx, class_name in enumerate(class_names):  # doorloop elke plantsoort
        folder = os.path.join(test_dir, class_name)  # map van die soort

        for img_name in os.listdir(folder):  # alle afbeeldingen in de map
            if not img_name.lower().endswith((".jpg", ".jpeg", ".png")):
                continue  # skip niet-afbeeldingen

            img_path = os.path.join(folder, img_name)  # volledig pad
            try:
                image = Image.open(img_path).convert("RGB")  # afbeelding openen
            except Exception as e:
                print(f"⚠️ Kan afbeelding niet openen: {img_path} ({e})")  # melding bij fout
                continue

            img_t = transform(image).unsqueeze(0)  # transformeren naar modelinput
            with torch.no_grad():
                outputs = model(img_t)  # model runnen
                pred_idx = outputs.argmax(1).item()  # hoogste score pakken

            y_true.append(idx)  # echt label opslaan
            y_pred.append(pred_idx)  # voorspeld label opslaan
            total += 1  # teller verhogen

            if pred_idx == idx:
                correct += 1  # juist voorspeld
            else:
                misclassified.append((img_path, class_name, class_names[pred_idx]))  # fout toevoegen

            print(f"📸 {img_name}: verwacht '{class_name}' → voorspeld '{class_names[pred_idx]}'")  # resultaat tonen

    # ==========================================
    # Resultaten en CSV
    # ==========================================

    accuracy = 100 * correct / total if total > 0 else 0  # nauwkeurigheid berekenen
    print(f"\n✅ Test voltooid — Nauwkeurigheid: {accuracy:.2f}% ({correct}/{total})")  # print score
    print(f"Aantal misclassificaties: {len(misclassified)}")  # aantal fouten tonen

    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:  # CSV-bestand aanmaken
        writer = csv.writer(csvfile)
        writer.writerow(["image_path", "true_label", "predicted_label"])  # kolomnamen
        for row in misclassified:
            writer.writerow(row)  # elke fout opslaan
    print(f"📁 Misclassificaties opgeslagen in: {output_csv}")  # bevestiging

    # ==========================================
    # Confusion matrix
    # ==========================================

    if total > 0:  # alleen als er iets getest is
        cm = confusion_matrix(y_true, y_pred, labels=list(range(num_classes)))  # matrix berekenen
        cm_norm = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis]  # normaliseren per rij
        cm_norm = np.nan_to_num(cm_norm)  # NaN vervangen door 0

        fig, ax = plt.subplots(figsize=(8, 6))  # plot aanmaken
        im = ax.imshow(cm_norm, interpolation='nearest', cmap="viridis")  # heatmap tekenen
        ax.figure.colorbar(im, ax=ax)  # kleurenschaal toevoegen

        ax.set(
            xticks=np.arange(num_classes),
            yticks=np.arange(num_classes),
            xticklabels=class_names,
            yticklabels=class_names,
            ylabel="Echte klasse",
            xlabel="Voorspelde klasse",
            title="Genormaliseerde confusion matrix"
        )

        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")  # x-labels schuin zetten

        thresh = cm_norm.max() / 2.  # drempel voor tekstkleur
        for i in range(cm_norm.shape[0]):
            for j in range(cm_norm.shape[1]):
                text = f"{cm[i, j]}"  # absolute aantallen tonen
                ax.text(j, i, text, ha="center", va="center",
                        color="white" if cm_norm[i, j] > thresh else "black")  # tekstcontrast aanpassen

        plt.tight_layout()  # layout optimaliseren
        plt.savefig(confusion_png)  # figuur opslaan
        plt.close()  # sluiten
        print(f"🧩 Confusion matrix opgeslagen als: {confusion_png}")  # bevestiging
