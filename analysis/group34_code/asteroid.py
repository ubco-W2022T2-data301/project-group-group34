import math
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

EPSILON = 1e-12  # precision for floating point comparisons
mass_sun = 1.989e30  # kg
g = 6.67408e-11  # Newton's gravitational constant


def solve_bisection(fn, xmin, xmax, epsilon=EPSILON):
    while True:
        xmid = (xmin + xmax) * 0.5
        if xmax - xmin < epsilon:
            return xmid
        fn_mid = fn(xmid)
        fn_min = fn(xmin)
        if fn_min * fn_mid < 0:
            xmax = xmid
        else:
            xmin = xmid


# from: https://en.wikipedia.org/wiki/Kepler%27s_laws_of_planetary_motion#Position_as_a_function_of_time
def position_at_time(orbit_axis, eccentricity, t):
    mu = g * mass_sun
    period = math.sqrt(orbit_axis ** 3 / mu)
    mean_anomaly = (t / period) % (2 * math.pi)
    eccentricty_anomaly = solve_bisection(lambda x: mean_anomaly - (x - eccentricity * math.sin(x)), 0, 2 * math.pi)
    theta = 2 * math.atan(
        math.sqrt((((1 + eccentricity) * math.tan(eccentricty_anomaly / 2) ** 2) / (1 - eccentricity))))
    if eccentricty_anomaly > math.pi:
        theta = 2 * math.pi - theta
    heliocentric_distance = orbit_axis * (1 - eccentricity * math.cos(eccentricty_anomaly))
    return theta, heliocentric_distance


def position_at_time_series(object_name: pd.Series, orbit_axis: pd.Series, eccentricity: pd.Series, t: float):
    mu = g * mass_sun
    period = orbit_axis.apply(lambda x: math.sqrt(x ** 3 / mu))
    mean_anomaly = (t / period) % (2 * math.pi)
    eccentricity_anomaly_list = []
    for index, value in enumerate(mean_anomaly):
        eccentricity_anomaly_list.append(solve_bisection(lambda x: value - (x - eccentricity[index] * math.sin(x)), 0,
                                                         2 * math.pi))
    theta_list = []
    heliocentric_distance_list = []
    for index, value in enumerate(eccentricity_anomaly_list):
        current_eccentricity = eccentricity.iat[index]
        theta_list.append(2 * math.atan(
            math.sqrt(((1 + current_eccentricity) * math.tan(value / 2) ** 2) / (1 - current_eccentricity))))
        if value > math.pi:
            theta_list[-1] = 2 * math.pi - theta_list[-1]
        heliocentric_distance_list.append(orbit_axis.iat[index] * (1 - current_eccentricity * math.cos(value)))

    df = pd.DataFrame(columns=["Theta (Radians)", "Heliocentric Distance (Au)"])
    df["Object Name"] = object_name
    df["Theta (Radians)"] = theta_list
    df["Heliocentric Distance (Au)"] = heliocentric_distance_list
    return df


def distance_between(body_1_theta, body_1_dist, body_2_theta, body_2_dist):
    # Convert polar coordinates to cartesian coordinates
    body_1_x = body_1_dist * math.cos(body_1_theta)
    body_1_y = body_1_dist * math.sin(body_1_theta)
    body_2_x = body_2_dist * math.cos(body_2_theta)
    body_2_y = body_2_dist * math.sin(body_2_theta)

    # Calculate distance using the distance formula
    return math.sqrt((body_2_x - body_1_x) ** 2 + (body_2_y - body_1_y) ** 2)


def time_to_seconds(close_approach_year, close_approach_month, close_approach_day, close_approach_hour,
                    close_approach_minute):
    return close_approach_year * 31536000 + close_approach_month * 2592000 + close_approach_day * 86400 + \
        close_approach_hour * 3600 + close_approach_minute * 60


def render_asteroid_trajectory(asteroid):
    ax = plt.figure(0).add_subplot(111, aspect='equal')

    plt.title('Inner Planetary Orbits')
    plt.ylabel('x10^6 km')
    plt.xlabel('x10^6 km')
    ax.set_xlim(-300, 1000)
    ax.set_ylim(-300, 300)
    plt.grid()

    ax.scatter(0, 0, s=200, color='y')
    plt.annotate('Sun', xy=(20, -50))

    def draw_planet(planet_position, colour):
        theta, dist = planet_position
        dist = dist * 149.6
        x = -dist * math.cos(theta)
        y = dist * math.sin(theta)
        planet = Circle((x, y), 3, color=colour)
        ax.add_artist(planet)

    eccentricity = asteroid["Orbit Eccentricity"]
    orbit_axis = asteroid["Orbit Axis (AU)"]
    close_approach_data = asteroid["Close-Approach (CA) Date"]

    close_approach_date = close_approach_data.split(" ")[0]  # format is "YYYY-MM-DD"
    close_approach_time = close_approach_data.split(" ")[1]  # format is "HH:MM"
    close_approach_year = int(close_approach_date.split("-")[0])
    close_approach_month = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, "Jul": 7, "Aug": 8, "Sep": 9,
                            "Oct": 10, "Nov": 11, "Dec": 12}[close_approach_date.split("-")[1]]
    close_approach_day = int(close_approach_date.split("-")[2])
    close_approach_hour = int(close_approach_time.split(":")[0])
    close_approach_minute = int(close_approach_time.split(":")[1])
    time_offset = time_to_seconds(close_approach_year, close_approach_month, close_approach_day,
                                  close_approach_hour, close_approach_minute)
    time_offset -= 365.25 * 24 * 60 * 60 * 1970
    duration = 365.25 * 24 * 60 * 60
    precision = 500
    distance_df = pd.DataFrame(columns=['Time', 'Distance'])
    for j in range(precision):
        seconds = j / precision * duration + time_offset
        earth_position_at_t = position_at_time(1.0000010178, 0.0167086, seconds - time_offset)
        asteroid_position_at_t = position_at_time(orbit_axis, eccentricity, seconds)
        draw_planet(earth_position_at_t, 'blue')
        draw_planet(asteroid_position_at_t, 'red')
        distance = distance_between(earth_position_at_t[0], earth_position_at_t[1],
                                    asteroid_position_at_t[0], asteroid_position_at_t[1])
        distance_df = pd.concat(
            [distance_df, pd.DataFrame([[seconds - time_offset, distance]], columns=['Time', 'Distance'])])

    plt.show()
