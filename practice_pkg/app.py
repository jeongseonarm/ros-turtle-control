import sys
import threading
import rclpy
from PyQt5.QtWidgets import QApplication

from practice_pkg.db_helper import DB, DB_CONFIG
from practice_pkg.turtle_node import TurtleControllerNode
from practice_pkg.main_window import MainWindow


def main(args=None):
    # 1. Initialize ROS 2 communication
    rclpy.init(args=args)

    # 2. Create DB and ROS Node instances
    db = DB(**DB_CONFIG)
    node = TurtleControllerNode()

    # 3. Run ROS 2 spin in background thread to prevent blocking GUI
    ros_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    ros_thread.start()

    # 4. Create PyQt5 application and display main window
    app = QApplication(sys.argv)
    main_window = MainWindow(node, db)
    main_window.show()

    # 5. Wait for GUI exit event
    exit_code = app.exec_()

    # 6. Clean up resources and shutdown ROS 2
    node.destroy_node()
    rclpy.shutdown()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()