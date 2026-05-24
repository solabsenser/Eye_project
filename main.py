import cv2
import mediapipe as mp
import time

# MediaPipe
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    refine_landmarks=True,
    max_num_faces=1
)

# Камера
cap = cv2.VideoCapture(0)

# HD качество
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# Радужка
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]
# Веки
LEFT_EYE_TOP = 159
LEFT_EYE_BOTTOM = 145

# Калибровка
calibration_stage = "LEFT"
left_value = None
right_value = None
top_value = None
bottom_value = None

selected = "CENTER"

# Dwell selection
last_selection = None
selection_start = time.time()
confirmed = ""
blink_detected = False

# Текст
typed_text = ""

# Курсор
cursor_x = 640
cursor_y = 360

while True:

    success, frame = cap.read()

    if not success:
        break

    frame = cv2.flip(frame, 1)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = face_mesh.process(rgb_frame)

    h, w, _ = frame.shape

    avg_x = None
    avg_y = None
    
    if results.multi_face_landmarks:

        face_landmarks = results.multi_face_landmarks[0]

        iris_x_total = []

        # Левый глаз
        for idx in LEFT_IRIS:

            landmark = face_landmarks.landmark[idx]

            x = int(landmark.x * w)
            y = int(landmark.y * h)

            iris_x_total.append(x)

            cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

        # Правый глаз
        for idx in RIGHT_IRIS:

            landmark = face_landmarks.landmark[idx]

            x = int(landmark.x * w)
            y = int(landmark.y * h)

            iris_x_total.append(x)

            cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

        avg_x = sum(iris_x_total) / len(iris_x_total)

        # Левый глаз
        iris_y_total = []

        for idx in LEFT_IRIS + RIGHT_IRIS:

            landmark = face_landmarks.landmark[idx]

            y = int(landmark.y * h)

            iris_y_total.append(y)

        avg_y = sum(iris_y_total) / len(iris_y_total)
        
        # Blink detection
        top_lid = face_landmarks.landmark[LEFT_EYE_TOP]
        bottom_lid = face_landmarks.landmark[LEFT_EYE_BOTTOM]

        top_y = int(top_lid.y * h)
        bottom_y = int(bottom_lid.y * h)

        blink_distance = abs(top_y - bottom_y)
        
    # ---------- КАЛИБРОВКА ----------

    if calibration_stage == "LEFT":

        cv2.putText(
            frame,
            "LOOK LEFT AND PRESS SPACE",
            (50, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 255),
            3
        )

    elif calibration_stage == "RIGHT":

        cv2.putText(
            frame,
            "LOOK RIGHT AND PRESS SPACE",
            (50, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 255),
            3
        )

    elif calibration_stage == "TOP":

        cv2.putText(
            frame,
            "LOOK UP AND PRESS SPACE",
            (50, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 0, 255),
            3
        )

    elif calibration_stage == "BOTTOM":

        cv2.putText(
            frame,
            "LOOK DOWN AND PRESS SPACE",
            (50, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 0, 255),
            3
        )
    
    else:

        selected = "CENTER"

        if avg_x is not None:

            # Нормализация взгляда
            gaze_ratio = (avg_x - left_value) / (right_value - left_value)
            gaze_ratio_y = (avg_y - top_value) / (bottom_value - top_value)

            gaze_ratio_y = max(0, min(1, gaze_ratio_y))

            # Ограничение
            gaze_ratio = max(0, min(1, gaze_ratio))

            # Позиция курсора
            # Целевая позиция
            target_x = int(gaze_ratio * w)
            target_y = int(gaze_ratio_y * h)

            # Сглаживание
            smoothness = 0.15

            cursor_x += int((target_x - cursor_x) * smoothness)
            cursor_y += int((target_y - cursor_y) * smoothness)

            # Кнопки
            buttons = [
                ("YES", (50, 500, 280, 650)),
                ("NO", (330, 500, 560, 650)),
                ("HELLO", (610, 500, 840, 650)),
                ("EXIT", (890, 500, 1120, 650))
            ]

            # Проверка наведения курсора
            for button_name, (x1, y1, x2, y2) in buttons:

                if x1 < cursor_x < x2 and y1 < cursor_y < y2:
                    selected = button_name
                    
            # Проверка моргания
            if blink_distance < 5:
                blink_detected = True
            else:
                blink_detected = False
                
            # Проверка удержания взгляда
            if selected != last_selection:

                last_selection = selected
                selection_start = time.time()

            else:

                duration = time.time() - selection_start

                if duration > 1 or blink_detected:

                    confirmed = selected

                    if confirmed == "YES":
                        typed_text += " YES"

                    elif confirmed == "NO":
                        typed_text += " NO"

                    elif confirmed == "HELLO":
                        typed_text += " HELLO"

                    elif confirmed == "EXIT":
                        break

                    # Защита от повторов
                    selection_start = time.time() + 1

        # ---------- ОТРИСОВКА КНОПОК ----------

        buttons = [
            ("YES", (50, 500, 280, 650)),
            ("NO", (330, 500, 560, 650)),
            ("HELLO", (610, 500, 840, 650)),
            ("EXIT", (890, 500, 1120, 650))
        ]

        for button_name, (x1, y1, x2, y2) in buttons:

            color = (255, 255, 255)

            if selected == button_name:
                color = (0, 255, 0)

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                color,
                -1
            )

            cv2.putText(
                frame,
                button_name,
                (x1 + 20, y1 + 85),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.5,
                (0, 0, 0),
                4
            )

        # ---------- КУРСОР ----------

        cv2.circle(
            frame,
            (cursor_x, cursor_y),
            15,
            (255, 0, 255),
            -1
        )

        # ---------- UI ----------

        cv2.putText(
            frame,
            f"TEXT:{typed_text}",
            (50, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 0),
            3
        )

        cv2.putText(
            frame,
            f"SELECTED: {selected}",
            (50, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"CONFIRMED: {confirmed}",
            (50, 150),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 0),
            2
        )

    # FULLSCREEN
    cv2.namedWindow(
        "Eye Tracking Calibration",
        cv2.WND_PROP_FULLSCREEN
    )

    cv2.setWindowProperty(
        "Eye Tracking Calibration",
        cv2.WND_PROP_FULLSCREEN,
        cv2.WINDOW_FULLSCREEN
    )

    cv2.imshow("Eye Tracking Calibration", frame)

    key = cv2.waitKey(1)

    # ESC
    if key == 27:
        break

    # SPACE
    if key == 32 and avg_x is not None:

        if calibration_stage == "LEFT":

            left_value = avg_x
            calibration_stage = "RIGHT"

        elif calibration_stage == "RIGHT":

            right_value = avg_x
            calibration_stage = "TOP"

        elif calibration_stage == "TOP":

            top_value = avg_y
            calibration_stage = "BOTTOM"

        elif calibration_stage == "BOTTOM":

            bottom_value = avg_y
            calibration_stage = "DONE"
            
cap.release()
cv2.destroyAllWindows()
