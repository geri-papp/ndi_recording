import cv2


def main():

    img = cv2.imread("results_0.jpg", cv2.IMREAD_COLOR)
    cv2.imshow('asd', img)
    cv2.waitKey(0)


if __name__ == "__main__":
    main()
