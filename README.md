# Python Photon Library

Python version of library for [Photon](https://www.exitgames.com/)

This version specifics:

- works only with TCP protocol
- doesn't support encrypted connection
- doesn't collect traffic stats

Python version is 3.4


# Example

    import threading
    import time
    
    from photon import enums
    
    from photon.enums import DebugLevel, StatusCode
    from photon.listener import PeerListener
    from photon.peer import PhotonPeer
    
    
    class Connection:
        def __init__(self, connected=False):
            self.connected = connected
    
    
    def main():
        connection = Connection()
    
        pp = PhotonPeer(enums.ConnectionProtocol.Tcp, SimpleListener(connection))
        pp.set_debug_level(DebugLevel.All)
    
        pp.connect(your_ip, your_port, your_app_name)
    
        service_thread = ServiceThread(pp)
        service_thread.start()
    
        while connection.connected is False:
            pass
        
        # Put your code here   
    
        service_thread.stop()
        service_thread.join()
    
        pp.disconnect()
    
    
    class ServiceThread(threading.Thread):
        def __init__(self, pp):
            threading.Thread.__init__(self)
    
            self.pp = pp
            self._run = False
    
        def run(self):
            self._run = True
    
            while self._run:
                self.pp.service()
    
                time.sleep(100.0 / 1000.0)
    
        def stop(self):
            self._run = False
    
    
    class SimpleListener(PeerListener):
        def __init__(self, connection):
            super().__init__()
            self.connection = connection
    
        def debug_return(self, debug_level, message):
            print("[{}] - {}".format(debug_level.name, message))
    
        def on_status_changed(self, status_code):
            print("[Status changed] - {}".format(status_code.name))
            if status_code is StatusCode.Connect:
                self.connection.connected = True
    
        def on_operation_response(self, op_response):
            print(op_response)
    
        def on_event(self, event_data):
            print(op_response)
    
    
    if __name__ == "__main__":
        main()