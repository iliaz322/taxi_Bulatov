document.addEventListener("DOMContentLoaded", () => {
  // Управление масштабом текста на всём сайте.
  const textScaleKey = "taxigo-text-scale";
  const textScaleButtons = [...document.querySelectorAll("[data-text-scale-button]")];
  const availableTextScales = ["sm", "md", "lg"];

  const applyTextScale = (scale) => {
    const safeScale = availableTextScales.includes(scale) ? scale : "md";
    document.documentElement.dataset.textScale = safeScale;
    textScaleButtons.forEach((button) => {
      const isActive = button.dataset.textScaleButton === safeScale;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-pressed", String(isActive));
    });

    try {
      localStorage.setItem(textScaleKey, safeScale);
    } catch (error) {
      // Ничего не делаем, если localStorage недоступен.
    }
  };

  if (textScaleButtons.length) {
    const currentScale = document.documentElement.dataset.textScale || "md";
    applyTextScale(currentScale);

    textScaleButtons.forEach((button) => {
      button.addEventListener("click", () => {
        applyTextScale(button.dataset.textScaleButton);
      });
    });
  }

  // Раскрытие списка машин для тарифов на главной.
  const tariffCards = [...document.querySelectorAll("[data-tariff-card]")];
  if (tariffCards.length) {
    tariffCards.forEach((card) => {
      const toggle = card.querySelector("[data-tariff-toggle]");
      const details = card.querySelector("[data-tariff-details]");

      if (!toggle || !details) {
        return;
      }

      toggle.addEventListener("click", () => {
        const isOpen = toggle.getAttribute("aria-expanded") === "true";
        toggle.setAttribute("aria-expanded", String(!isOpen));
        details.hidden = isOpen;
        toggle.textContent = isOpen ? "Какие машины могут приехать" : "Скрыть список машин";
      });
    });
  }

  // Предпросмотр выбранной аватарки в профиле.
  const avatarInput = document.getElementById("id_avatar");
  const avatarFileName = document.getElementById("avatar-file-name");
  const avatarPreview = document.getElementById("account-avatar-preview");
  const avatarPlaceholder = document.getElementById("account-avatar-placeholder");

  if (avatarInput) {
    avatarInput.addEventListener("change", () => {
      const file = avatarInput.files?.[0];

      if (!file) {
        if (avatarFileName) {
          avatarFileName.textContent = "Файл пока не выбран";
        }
        return;
      }

      if (avatarFileName) {
        avatarFileName.textContent = `Выбран файл: ${file.name}`;
      }

      if (!file.type.startsWith("image/")) {
        return;
      }

      const reader = new FileReader();
      reader.onload = (event) => {
        const result = event.target?.result;
        if (typeof result !== "string") {
          return;
        }

        if (avatarPreview) {
          avatarPreview.src = result;
          return;
        }

        if (avatarPlaceholder) {
          const previewImage = document.createElement("img");
          previewImage.id = "account-avatar-preview";
          previewImage.className = "account-avatar-image";
          previewImage.src = result;
          previewImage.alt = "Аватар пользователя";
          avatarPlaceholder.replaceWith(previewImage);
        }
      };
      reader.readAsDataURL(file);
    });
  }

  // Автоматически скрываем flash-сообщения через 3 секунды.
  const messages = document.getElementById("messages");
  if (messages) {
    setTimeout(() => {
      messages.style.opacity = "0";
      messages.style.transition = "opacity 0.2s ease";
      setTimeout(() => messages.remove(), 200);
    }, 3000);
  }

  // Калькулятор цены на странице заказа.
  const tariffsNode = document.getElementById("tariffs-data");
  const tariffSelect = document.getElementById("id_tariff");
  const distanceInput = document.getElementById("id_distance_km");
  const minPriceNode = document.getElementById("calc-min-price");
  const pricePerKmNode = document.getElementById("calc-price-per-km");
  const totalNode = document.getElementById("calc-total");

  if (tariffsNode && tariffSelect && distanceInput) {
    const tariffs = JSON.parse(tariffsNode.textContent);
    const includedDistance = 2;
    const distanceMultipliers = [
      { threshold: 35, factor: 1.2 },
      { threshold: 20, factor: 1.11 },
      { threshold: 10, factor: 1.05 },
    ];

    const getFactor = (distance) => {
      const matched = distanceMultipliers.find((item) => distance > item.threshold);
      return matched ? matched.factor : 1;
    };

    const updateCalculator = () => {
      const selectedId = Number(tariffSelect.value);
      const distance = Number(String(distanceInput.value).replace(",", ".")) || 0;
      const tariff = tariffs.find((item) => item.id === selectedId);
      if (!tariff) {
        return;
      }

      const minPrice = Number(tariff.min_price);
      const pricePerKm = Number(tariff.price_per_km);
      const paidDistance = Math.max(distance - includedDistance, 0);
      const factor = getFactor(distance);
      const total = (minPrice + paidDistance * pricePerKm) * factor;

      minPriceNode.textContent = `${minPrice.toFixed(2).replace(".", ",")} ₽`;
      pricePerKmNode.textContent = `${pricePerKm.toFixed(2).replace(".", ",")} ₽`;
      totalNode.textContent = `${total.toFixed(2).replace(".", ",")} ₽`;
    };

    tariffSelect.addEventListener("change", updateCalculator);
    distanceInput.addEventListener("input", updateCalculator);
    updateCalculator();
  }

  // Выбор точек на Яндекс.Карте и расчет маршрута по дорогам через OSRM.
  const mapContainer = document.getElementById("ride-map");
  if (mapContainer && window.ymaps) {
    const fromInput = document.getElementById("id_from_address");
    const toInput = document.getElementById("id_to_address");
    const helperText = document.getElementById("map-helper-text");
    const modeButtons = [...document.querySelectorAll("[data-map-mode]")];
    const clearButton = document.getElementById("clear-map-route");
    const addressTimers = { from: null, to: null };
    const geocodeTokens = { from: 0, to: 0 };

    let mapMode = "from";
    let fromCoords = null;
    let toCoords = null;
    let fromPlacemark = null;
    let toPlacemark = null;
    let routeLine = null;
    let isRouting = false;

    const formatDistance = (meters) => (meters / 1000).toFixed(1);

    const haversineDistance = (coordA, coordB) => {
      const toRad = (value) => (value * Math.PI) / 180;
      const [lat1, lon1] = coordA;
      const [lat2, lon2] = coordB;
      const earthRadius = 6371000;
      const dLat = toRad(lat2 - lat1);
      const dLon = toRad(lon2 - lon1);
      const a =
        Math.sin(dLat / 2) ** 2 +
        Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
      return earthRadius * c;
    };

    const setMode = (mode) => {
      mapMode = mode;
      modeButtons.forEach((button) => {
        button.classList.toggle("is-active", button.dataset.mapMode === mode);
      });
      if (helperText) {
        helperText.textContent =
          mode === "from"
            ? "Сейчас выберите точку отправления на карте."
            : "Сейчас выберите точку назначения на карте.";
      }
    };

    const setInputValue = (input, value) => {
      if (!input) return;
      input.value = value;
      input.dispatchEvent(new Event("change", { bubbles: true }));
    };

    const formatCoords = (coords) => `${coords[0].toFixed(5)}, ${coords[1].toFixed(5)}`;

    const parseCoordsFromInput = (value) => {
      const matched = value.match(/^\s*(-?\d+(?:[.,]\d+)?)\s*,\s*(-?\d+(?:[.,]\d+)?)\s*$/);
      if (!matched) {
        return null;
      }

      return [Number(matched[1].replace(",", ".")), Number(matched[2].replace(",", "."))];
    };

    const updatePriceAfterDistance = () => {
      if (typeof tariffSelect?.dispatchEvent === "function") {
        distanceInput.dispatchEvent(new Event("input", { bubbles: true }));
      }
    };

    const resetRouteState = (map, message) => {
      if (routeLine) {
        map.geoObjects.remove(routeLine);
        routeLine = null;
      }

      distanceInput.value = "0.5";
      updatePriceAfterDistance();

      if (message && helperText) {
        helperText.textContent = message;
      }
    };

    const reverseGeocode = (coords, targetInput, fallbackPrefix) => {
      setInputValue(targetInput, `${fallbackPrefix}: ${formatCoords(coords)}`);

      window.ymaps
        .geocode(coords)
        .then((result) => {
          const firstGeoObject = result.geoObjects.get(0);
          if (!firstGeoObject) {
            return;
          }

          const metadata = firstGeoObject.properties.get("metaDataProperty");
          const geocoderText = metadata?.GeocoderMetaData?.text;
          const addressLine =
            typeof firstGeoObject.getAddressLine === "function"
              ? firstGeoObject.getAddressLine()
              : geocoderText;

          if (addressLine) {
            setInputValue(targetInput, addressLine);
          }
        })
        .catch(() => {
          setInputValue(targetInput, `${fallbackPrefix}: ${formatCoords(coords)}`);
        });
    };

    const drawFallbackRoute = (map) => {
      if (!fromCoords || !toCoords) return;

      const directMeters = haversineDistance(fromCoords, toCoords);
      const roadMeters = directMeters * 1.18;
      distanceInput.value = formatDistance(roadMeters);

      if (routeLine) {
        map.geoObjects.remove(routeLine);
      }

      routeLine = new window.ymaps.Polyline([fromCoords, toCoords], {}, {
        strokeColor: "#1C1C1E",
        strokeWidth: 4,
        strokeOpacity: 0.85,
      });
      map.geoObjects.add(routeLine);

      const bounds = window.ymaps.util.bounds.fromPoints([fromCoords, toCoords]);
      map.setBounds(bounds, { checkZoomRange: true, zoomMargin: 40 });
      updatePriceAfterDistance();

      if (helperText) {
        helperText.textContent = `Маршрут построен приблизительно. Расстояние: ${formatDistance(roadMeters)} км.`;
      }
    };

    const buildRoadRoute = async (map) => {
      if (!fromCoords || !toCoords || isRouting) return;
      isRouting = true;

      if (helperText) {
        helperText.textContent = "Строим маршрут по дорогам…";
      }

      const fromLonLat = `${fromCoords[1]},${fromCoords[0]}`;
      const toLonLat = `${toCoords[1]},${toCoords[0]}`;
      const routeUrl = `https://router.project-osrm.org/route/v1/driving/${fromLonLat};${toLonLat}?overview=full&geometries=geojson`;

      try {
        const response = await fetch(routeUrl);
        if (!response.ok) {
          throw new Error("Route request failed");
        }

        const payload = await response.json();
        const route = payload.routes?.[0];
        if (!route?.geometry?.coordinates?.length) {
          throw new Error("Route geometry missing");
        }

        const routeCoords = route.geometry.coordinates.map(([lon, lat]) => [lat, lon]);
        distanceInput.value = formatDistance(route.distance);

        if (routeLine) {
          map.geoObjects.remove(routeLine);
        }

        routeLine = new window.ymaps.Polyline(routeCoords, {}, {
          strokeColor: "#1C1C1E",
          strokeWidth: 4,
          strokeOpacity: 0.9,
        });
        map.geoObjects.add(routeLine);

        const bounds = window.ymaps.util.bounds.fromPoints(routeCoords);
        map.setBounds(bounds, { checkZoomRange: true, zoomMargin: 40 });
        updatePriceAfterDistance();

        if (helperText) {
          helperText.textContent = `Маршрут по дорогам построен. Расстояние: ${formatDistance(route.distance)} км.`;
        }
      } catch (error) {
        drawFallbackRoute(map);
        if (helperText) {
          helperText.textContent = "Не удалось получить маршрут по дорогам. Показан приблизительный маршрут.";
        }
      } finally {
        isRouting = false;
      }
    };

    window.ymaps.ready(() => {
      const map = new window.ymaps.Map("ride-map", {
        center: [55.751244, 37.618423],
        zoom: 10,
        controls: ["zoomControl", "geolocationControl"],
      });

      const syncPlacemark = (kind, coords) => {
        const placemarkKey = kind === "from" ? "Откуда" : "Куда";
        const preset =
          kind === "from" ? "islands#blackDotIconWithCaption" : "islands#yellowDotIconWithCaption";
        const currentPlacemark = kind === "from" ? fromPlacemark : toPlacemark;

        if (currentPlacemark) {
          map.geoObjects.remove(currentPlacemark);
        }

        const nextPlacemark = new window.ymaps.Placemark(
          coords,
          { iconCaption: placemarkKey },
          { preset }
        );
        map.geoObjects.add(nextPlacemark);

        if (kind === "from") {
          fromPlacemark = nextPlacemark;
          fromCoords = coords;
        } else {
          toPlacemark = nextPlacemark;
          toCoords = coords;
        }
      };

      const syncAddressToMap = (kind, options = {}) => {
        const targetInput = kind === "from" ? fromInput : toInput;
        const targetValue = targetInput.value.trim();
        const shouldFocus = options.focus !== false;
        const parsedCoords = parseCoordsFromInput(targetValue);

        if (!targetValue) {
          if (kind === "from") {
            fromCoords = null;
            if (fromPlacemark) {
              map.geoObjects.remove(fromPlacemark);
              fromPlacemark = null;
            }
          } else {
            toCoords = null;
            if (toPlacemark) {
              map.geoObjects.remove(toPlacemark);
              toPlacemark = null;
            }
          }

          if (!fromCoords || !toCoords) {
            resetRouteState(map, "Введите оба адреса или выберите две точки на карте.");
          }
          return;
        }

        if (parsedCoords) {
          syncPlacemark(kind, parsedCoords);

          if (fromCoords && toCoords) {
            buildRoadRoute(map);
          } else if (shouldFocus) {
            map.setCenter(parsedCoords, 13, { duration: 250 });
          }
          return;
        }

        const token = Date.now();
        geocodeTokens[kind] = token;

        if (helperText) {
          helperText.textContent =
            kind === "from"
              ? "Ищем точку отправления по введенному адресу…"
              : "Ищем точку назначения по введенному адресу…";
        }

        window.ymaps
          .geocode(targetValue, { results: 1 })
          .then((result) => {
            if (geocodeTokens[kind] !== token) {
              return;
            }

            const firstGeoObject = result.geoObjects.get(0);
            if (!firstGeoObject) {
              throw new Error("Address not found");
            }

            const coords = firstGeoObject.geometry.getCoordinates();
            syncPlacemark(kind, coords);

            if (shouldFocus) {
              if (fromCoords && toCoords) {
                buildRoadRoute(map);
              } else {
                map.setCenter(coords, 13, { duration: 250 });
                if (helperText) {
                  helperText.textContent =
                    kind === "from"
                      ? "Точка отправления найдена. Теперь укажите адрес назначения."
                      : "Точка назначения найдена. Теперь укажите адрес отправления.";
                }
              }
            } else if (fromCoords && toCoords) {
              buildRoadRoute(map);
            }
          })
          .catch(() => {
            if (geocodeTokens[kind] !== token) {
              return;
            }

            if (helperText) {
              helperText.textContent =
                kind === "from"
                  ? "Не удалось найти точку отправления. Уточните адрес или выберите место на карте."
                  : "Не удалось найти точку назначения. Уточните адрес или выберите место на карте.";
            }
          });
      };

      const scheduleAddressSync = (kind) => {
        if (addressTimers[kind]) {
          clearTimeout(addressTimers[kind]);
        }

        addressTimers[kind] = setTimeout(() => {
          syncAddressToMap(kind);
        }, 450);
      };

      map.events.add("click", (event) => {
        const coords = event.get("coords");

        if (mapMode === "from") {
          syncPlacemark("from", coords);
          reverseGeocode(coords, fromInput, "Точка отправления");
          if (!toCoords) {
            setMode("to");
          }
        } else {
          syncPlacemark("to", coords);
          reverseGeocode(coords, toInput, "Точка назначения");
          setMode("from");
        }

        buildRoadRoute(map);
      });

      modeButtons.forEach((button) => {
        button.addEventListener("click", () => setMode(button.dataset.mapMode));
      });

      clearButton?.addEventListener("click", () => {
        fromCoords = null;
        toCoords = null;
        fromInput.value = "";
        toInput.value = "";
        [fromPlacemark, toPlacemark, routeLine].forEach((object) => {
          if (object) {
            map.geoObjects.remove(object);
          }
        });
        fromPlacemark = null;
        toPlacemark = null;
        routeLine = null;
        setMode("from");
        resetRouteState(map, "Сначала выберите точку отправления на карте.");
      });

      [["from", fromInput], ["to", toInput]].forEach(([kind, input]) => {
        input?.addEventListener("input", () => scheduleAddressSync(kind));
        input?.addEventListener("change", () => syncAddressToMap(kind));
        input?.addEventListener("blur", () => syncAddressToMap(kind));
        input?.addEventListener("keydown", (event) => {
          if (event.key === "Enter") {
            event.preventDefault();
            syncAddressToMap(kind);
          }
        });
      });

      if (fromInput?.value.trim()) {
        syncAddressToMap("from", { focus: false });
      }
      if (toInput?.value.trim()) {
        syncAddressToMap("to", { focus: false });
      }
    });
  }

  // Демо-трекинг водителя на странице статуса поездки.
  const statusMapContainer = document.getElementById("ride-status-map");
  const trackingPayloadNode = document.getElementById("ride-tracking-payload");
  if (statusMapContainer && trackingPayloadNode && window.ymaps) {
    const etaNode = document.getElementById("tracking-eta");
    const distanceNode = document.getElementById("tracking-distance");
    const modeNode = document.getElementById("tracking-mode-label");
    const statusPillNode = document.querySelector(".status-pill");
    const demoCsrfNode = document.getElementById("ride-demo-csrf");

    const payload = JSON.parse(trackingPayloadNode.textContent);
    const formatKm = (meters) => `${(meters / 1000).toFixed(1)} км`;
    const formatMinutes = (seconds) => {
      const minutes = Math.max(1, Math.round(seconds / 60));
      return `${minutes} мин`;
    };
    const getSeedOffset = (seed, multiplier, shift) => {
      const value = Math.sin(seed * multiplier) * shift;
      return Number(value.toFixed(4));
    };

    window.ymaps.ready(() => {
      const map = new window.ymaps.Map("ride-status-map", {
        center: [55.751244, 37.618423],
        zoom: 11,
        controls: ["zoomControl"],
      });

      const geocodeAddress = async (address) => {
        const result = await window.ymaps.geocode(address, { results: 1 });
        const firstGeoObject = result.geoObjects.get(0);
        if (!firstGeoObject) {
          throw new Error("Address not found");
        }
        return firstGeoObject.geometry.getCoordinates();
      };

      const buildRoute = async (fromCoords, toCoords) => {
        const fromLonLat = `${fromCoords[1]},${fromCoords[0]}`;
        const toLonLat = `${toCoords[1]},${toCoords[0]}`;
        const routeUrl = `https://router.project-osrm.org/route/v1/driving/${fromLonLat};${toLonLat}?overview=full&geometries=geojson`;
        const response = await fetch(routeUrl);
        if (!response.ok) {
          throw new Error("Tracking route failed");
        }
        const routePayload = await response.json();
        const route = routePayload.routes?.[0];
        if (!route?.geometry?.coordinates?.length) {
          throw new Error("Tracking geometry missing");
        }
        return {
          distance: route.distance,
          duration: route.duration,
          coords: route.geometry.coordinates.map(([lon, lat]) => [lat, lon]),
        };
      };

      const getPointAtProgress = (coords, progress) => {
        const index = Math.min(coords.length - 1, Math.max(0, Math.round((coords.length - 1) * progress)));
        return coords[index];
      };

      const getMockDriverOrigin = (anchorCoords) => [
        anchorCoords[0] + getSeedOffset(payload.rideId, 1.73, 0.08),
        anchorCoords[1] + getSeedOffset(payload.rideId, 2.37, 0.12),
      ];
      let completionPersisted = payload.status === "completed";

      const persistCompletion = async () => {
        if (completionPersisted || !payload.completeUrl) {
          return;
        }

        completionPersisted = true;

        try {
          const response = await fetch(payload.completeUrl, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": demoCsrfNode?.value || "",
            },
            credentials: "same-origin",
            body: JSON.stringify({ source: "demo-tracking" }),
          });

          if (!response.ok) {
            throw new Error("Completion sync failed");
          }
        } catch (error) {
          completionPersisted = false;
        }
      };

      const setStatusPill = (status) => {
        if (!statusPillNode) return;
        statusPillNode.classList.remove(
          "status-searching",
          "status-active",
          "status-completed",
          "status-cancelled"
        );
        statusPillNode.classList.add(`status-${status}`);

        if (status === "searching") {
          statusPillNode.textContent = "Поиск";
        } else if (status === "active") {
          statusPillNode.textContent = "В пути";
        } else if (status === "completed") {
          statusPillNode.textContent = "Завершена";
        }
      };

      const animateRoute = ({ route, driverMarker, onFrame, onComplete, minDuration = 9000, maxDuration = 22000 }) => {
        const simulatedDuration = Math.max(minDuration, Math.min(maxDuration, route.duration * 140));
        const startedAt = performance.now();

        const tick = (now) => {
          const elapsed = now - startedAt;
          const progress = Math.min(elapsed / simulatedDuration, 1);
          const currentCoords = getPointAtProgress(route.coords, progress);
          driverMarker.geometry.setCoordinates(currentCoords);
          onFrame?.(progress, route);

          if (progress < 1) {
            requestAnimationFrame(tick);
          } else {
            onComplete?.(route);
          }
        };

        requestAnimationFrame(tick);
      };

      const startTracking = async () => {
        try {
          const fromCoords = await geocodeAddress(payload.fromAddress);
          const toCoords = await geocodeAddress(payload.toAddress);
          const headingToDestination = payload.status === "active" || payload.status === "completed";
          const routeStart = headingToDestination ? fromCoords : getMockDriverOrigin(fromCoords);
          const routeEnd = headingToDestination ? toCoords : fromCoords;

          const [approachRoute, tripRoute] = await Promise.all([
            buildRoute(routeStart, routeEnd),
            buildRoute(fromCoords, toCoords),
          ]);

          const pickupPlacemark = new window.ymaps.Placemark(
            fromCoords,
            { iconCaption: "Подача" },
            { preset: "islands#blackDotIconWithCaption" }
          );
          const destinationPlacemark = new window.ymaps.Placemark(
            toCoords,
            { iconCaption: "Маршрут" },
            { preset: "islands#yellowDotIconWithCaption" }
          );

          const tripPolyline = new window.ymaps.Polyline(tripRoute.coords, {}, {
            strokeColor: "#CFCFD3",
            strokeWidth: 5,
            strokeOpacity: 0.9,
          });
          const activePolyline = new window.ymaps.Polyline(approachRoute.coords, {}, {
            strokeColor: "#1C1C1E",
            strokeWidth: 5,
            strokeOpacity: 0.95,
          });

          const driverMarker = new window.ymaps.Placemark(
            routeStart,
            {
              iconCaption: payload.driverName || "Водитель",
              balloonContent: "Машина в пути",
            },
            {
              iconLayout: "default#image",
              iconImageHref: payload.carIconUrl,
              iconImageSize: [56, 56],
              iconImageOffset: [-28, -52],
            }
          );

          map.geoObjects.add(tripPolyline);
          map.geoObjects.add(activePolyline);
          map.geoObjects.add(pickupPlacemark);
          map.geoObjects.add(destinationPlacemark);
          map.geoObjects.add(driverMarker);

          const allBounds = window.ymaps.util.bounds.fromPoints([
            ...tripRoute.coords,
            ...approachRoute.coords,
          ]);
          map.setBounds(allBounds, { checkZoomRange: true, zoomMargin: 48 });

          if (modeNode) {
            modeNode.textContent = headingToDestination
              ? "Водитель везёт пассажира"
              : "Водитель едет на подачу";
          }

          const startTripPhase = () => {
            activePolyline.geometry.setCoordinates(tripRoute.coords);
            driverMarker.properties.set("balloonContent", "Пассажир в машине");
            setStatusPill("active");

            if (modeNode) {
              modeNode.textContent = "Водитель везёт пассажира";
            }

            animateRoute({
              route: tripRoute,
              driverMarker,
              minDuration: 12000,
              maxDuration: 26000,
              onFrame: (progress, route) => {
                const remainingDistance = route.distance * (1 - progress);
                const remainingDuration = route.duration * (1 - progress);

                if (etaNode) {
                  etaNode.textContent = progress >= 1 ? "Поездка завершена" : formatMinutes(remainingDuration);
                }
                if (distanceNode) {
                  distanceNode.textContent = progress >= 1 ? "0.0 км" : formatKm(remainingDistance);
                }
              },
              onComplete: () => {
                driverMarker.properties.set("balloonContent", "Поездка завершена");
                setStatusPill("completed");
                if (modeNode) {
                  modeNode.textContent = "Пассажир доставлен";
                }
                persistCompletion();
              },
            });
          };

          if (payload.status === "completed") {
            activePolyline.geometry.setCoordinates(tripRoute.coords);
            driverMarker.geometry.setCoordinates(toCoords);
            driverMarker.properties.set("balloonContent", "Поездка завершена");
            setStatusPill("completed");
            if (modeNode) {
              modeNode.textContent = "Пассажир доставлен";
            }
            if (etaNode) {
              etaNode.textContent = "Завершено";
            }
            if (distanceNode) {
              distanceNode.textContent = "0.0 км";
            }
            return;
          }

          if (headingToDestination) {
            startTripPhase();
            return;
          }

          animateRoute({
            route: approachRoute,
            driverMarker,
            onFrame: (progress, route) => {
              const remainingDistance = route.distance * (1 - progress);
              const remainingDuration = route.duration * (1 - progress);

              if (etaNode) {
                etaNode.textContent = progress >= 1 ? "Водитель на месте" : formatMinutes(remainingDuration);
              }
              if (distanceNode) {
                distanceNode.textContent = progress >= 1 ? "0.0 км" : formatKm(remainingDistance);
              }
            },
            onComplete: () => {
              driverMarker.properties.set("balloonContent", "Посадка завершена, начинается поездка");
              if (etaNode) {
                etaNode.textContent = "Пассажир сел в машину";
              }
              if (distanceNode) {
                distanceNode.textContent = formatKm(tripRoute.distance);
              }
              startTripPhase();
            },
          });
        } catch (error) {
          if (modeNode) {
            modeNode.textContent = "Трекинг временно недоступен";
          }
          if (etaNode) {
            etaNode.textContent = "—";
          }
          if (distanceNode) {
            distanceNode.textContent = "—";
          }
        }
      };

      startTracking();
    });
  }

  // Обработка рейтинга водителя через 5 звезд.
  const starsWrap = document.querySelector("[data-stars]");
  const ratingInput = document.getElementById("id_rating");
  if (starsWrap && ratingInput) {
    const stars = [...starsWrap.querySelectorAll("span")];

    const paint = (value) => {
      stars.forEach((star) => {
        star.classList.toggle("active", Number(star.dataset.value) <= value);
      });
    };

    stars.forEach((star) => {
      star.addEventListener("click", () => {
        const value = Number(star.dataset.value);
        ratingInput.value = value;
        paint(value);
      });
    });
  }
});
