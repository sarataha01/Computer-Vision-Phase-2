import numpy as np
from math import *
import time

#set stuck_time and donut_time with the current time
stuck_time = time.time()
donut_time = time.time()

# This is where you can build a decision tree for determining throttle, brake and steer 
# commands based on the output of the perception_step() function

#what will happen in case of stuck
def stuck(Rover):   
    global stuck_time
    Rover.throttle = 0
    #no brakes
    Rover.brake = 0
    #Turn either +15 or -15 degrees
    Rover.steer = -15
    return Rover


def decision_step(Rover):

    global stuck_time
    global donut_time
    
    offset = 0

    # Only apply left wall hugging when out of the starting point after 10s to avoid getting stuck in a circle
    if Rover.total_time > 10:
        # Steering proportional to the deviation results in
        # small offsets on straight lines and
        # large values in turns and open areas
        offset = 0.8 * np.std(Rover.nav_angles)
    
    #send pickup
    if Rover.near_sample and Rover.vel == 0 and not Rover.picking_up:
        Rover.send_pickup = True
        return Rover

    #STOP when near a sample
    if Rover.near_sample:
        Rover.mode = 'stop'
        Rover.throttle = 0
        Rover.brake = Rover.brake_set
        # Rover.send_pickup = True
        return Rover

    #if looping, break out of the loop
    if Rover.mode == "LargeCircleRotation":
        if time.time() - donut_time > 15: #15
            Rover.mode = "forward"
            donut_time=time.time()
        else:
            Rover.throttle = 0
            Rover.brake = 0
            Rover.steer = -10
        return Rover

    #detect if looping
    if Rover.steer==15 or Rover.steer==-15:
        #how long have we been doing circles
        if time.time() - donut_time > 10:  #more than 10 seconds
            Rover.mode = "LargeCircleRotation"
            return Rover
    else:
        donut_time=time.time()


    #Steer to direction of the sample
    if len(Rover.rock_angles) > 1:
            Rover.brake = Rover.brake_set
            Rover.mode = 'stop'
            Rover.steer = np.clip(np.mean(Rover.rock_angles * 180/np.pi), -15, 15)
            if (np.mean(Rover.rock_dists) >= 4):    #>
                Rover.throttle = 0.4
                Rover.brake = 0
            elif (np.mean(Rover.rock_dists) <= 4):  #<
                Rover.brake = Rover.brake_set
                Rover.near_sample = True
            return Rover
    # Example:
    # Check if we have vision data to make decisions with
    
    if Rover.nav_angles is not None:
        
        # Check for Rover.mode status
        if Rover.mode == 'forward':
            # #check if STUCK under a rock but can see navigable terrain
            if Rover.vel <= 0.08 and Rover.throttle != 0 and (len(Rover.rock_angles) == 0):
                if time.time() - stuck_time > 1.5:
                    Rover = stuck(Rover)
                    return Rover
            #reset time spent stuck
            else:
                stuck_time = time.time()
            # Check the extent of navigable terrain
            if len(Rover.nav_angles) >= Rover.stop_forward:  
                # If mode is forward, navigable terrain looks good 
                # and velocity is below max, then throttle 
                if Rover.vel < Rover.max_vel:
                    # Set throttle value to throttle setting
                    Rover.throttle = Rover.throttle_set
                else: # Else coast
                    Rover.throttle = 0
                Rover.brake = 0
                # Set steering to average angle clipped to the range +/- 15
                try:
                    Rover.steer = np.clip(np.mean((Rover.nav_angles+offset) * 180/np.pi) + offset, -15, 15)
                except:
                    print("mean of nav angles caught an exception")
            # If there's a lack of navigable terrain pixels then go to 'stop' mode
            elif len(Rover.nav_angles) < Rover.stop_forward:
                    # Set mode to "stop" and hit the brakes!
                    Rover.throttle = 0
                    # Set brake to stored brake value
                    Rover.brake = Rover.brake_set
                    Rover.steer = np.clip(np.mean((Rover.nav_angles+offset) * 180/np.pi)+ offset, -15, 15)
                    Rover.mode = 'stop'

        # If we're already in "stop" mode then make different decisions
        elif Rover.mode == 'stop':
            # If we're in stop mode but still moving keep braking
            if len(Rover.rock_angles) > 1:
                Rover.brake = Rover.brake_set
                Rover.steer = np.clip(np.mean(Rover.rock_angles * 180/np.pi), -15, 15)
                if (np.mean(Rover.rock_dists) >= 3):
                    Rover.throttle = 0.2
                    Rover.brake = 0
                elif (np.mean(Rover.rock_dists) <= 3):
                    Rover.brake = Rover.brake_set
                    Rover.near_sample = True
                return Rover

            if Rover.vel > 0.2:
                Rover.throttle = 0
                Rover.brake = Rover.brake_set
                Rover.steer = 0
            # If we're not moving (vel < 0.2) then do something else
            elif Rover.vel <= 0.2:
                # Now we're stopped and we have vision data to see if there's a path forward
                if (len(Rover.nav_angles) < Rover.go_forward) and len(Rover.rock_angles) == 0:
                    Rover.throttle = 0
                    # Release the brake to allow turning
                    Rover.brake = 0
                    # Turn range is +/- 15 degrees, when stopped the next line will induce 4-wheel turning
                    Rover.steer = -15 # Could be more clever here about which way to turn
                # If we're stopped but see sufficient navigable terrain in front then go!
                if len(Rover.nav_angles) >= Rover.go_forward:
                    # Set throttle back to stored value
                    Rover.throttle = Rover.throttle_set
                    # Release the brake
                    Rover.brake = 0
                    # Set steer to mean angle
                    try:
                        Rover.steer = np.clip(np.mean((Rover.nav_angles+offset)  * 180/np.pi) + offset, -15, 15)
                    except:
                        print("mean of nav angles caught an exception")
                    Rover.mode = 'forward'
            if Rover.vel == 0 and Rover.steer == -15 and len(Rover.nav_angles) > 20 and len(Rover.rock_angles) == 0 :
                Rover.steer = 0
                Rover.throttle = 0.5
                Rover.mode = 'forward'



    # Just to make the rover do something 
    # even if no modifications have been made to the code
    else:
        Rover.throttle = 0 #Rover.throttle_set
        Rover.steer = 0
        Rover.brake = 0
        

    
    return Rover


