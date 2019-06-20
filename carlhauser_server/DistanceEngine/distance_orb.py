#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
# ==================== ------ STD LIBRARIES ------- ====================
import sys
import cv2
from typing import Dict, List
import traceback

# ==================== ------ PERSONAL LIBRARIES ------- ====================
sys.path.append(os.path.abspath(os.path.pardir))

import carlhauser_server.Configuration.database_conf as database_conf
import carlhauser_server.Configuration.distance_engine_conf as distance_engine_conf
import carlhauser_server.Configuration.feature_extractor_conf as feature_extractor_conf
import carlhauser_server.DistanceEngine.scoring_datastrutures as sd


class Distance_ORB:
    def __init__(self, db_conf: database_conf.Default_database_conf, dist_conf: distance_engine_conf.Default_distance_engine_conf, fe_conf: feature_extractor_conf.Default_feature_extractor_conf):
        # STD attributes
        self.logger = logging.getLogger(__name__)
        self.logger.info("Creation of a Distance ORB Engine")

        # Save configuration
        self.db_conf = db_conf  # TODO : REMOVE = NOT USEFUL FOR NOW !
        self.dist_conf = dist_conf
        self.fe_conf = fe_conf

        self.orb_matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=dist_conf.CROSSCHECK)

    def orb_distance(self, pic_package_from, pic_package_to):
        answer = {}
        self.logger.info("Orb distance computation ... ")

        try:
            # Note : @image must be a PIL instance.
            if self.fe_conf.ORB.get("is_enabled", False):
                answer = self.add_results(self.fe_conf.ORB, pic_package_from, pic_package_to, answer)

                '''
                # Compute matches
                matches = self.orb_matcher.match(pic_package_from["ORB_DESCRIPTORS"], pic_package_to["ORB_DESCRIPTORS"])

                answer["ORB_DISTANCE"] = self.max_dist(matches, self.threeshold_distance_filter(matches))
                '''

        except Exception as e:
            self.logger.error(traceback.print_tb(e.__traceback__))
            self.logger.error("Error during orbing : " + str(e))

        return answer

    def add_results(self, algo_conf: feature_extractor_conf.Algo_conf, pic_package_from, pic_package_to, answer: Dict) -> Dict:
        # Add results to answer dict, depending on the algorithm name we want to compute
        # Ex : Input {} -> Output {"ORB":{"name":"ORB", "distance":0.3,"decision":YES}}
        algo_name = algo_conf.get('algo_name')

        tmp_dist = self.compute_orb_distance(pic_package_from["ORB_DESCRIPTORS"], pic_package_to["ORB_DESCRIPTORS"])

        # Add the distance as an AlgoMatch
        answer[algo_name] = sd.AlgoMatch(name=algo_name,
                                         distance=tmp_dist,
                                         decision=self.compute_decision_from_distance(algo_conf, tmp_dist))
        return answer

    # ==================== ------ CORE COMPUTATION FOR ORB ------- ====================

    def compute_orb_distance(self, descriptors_1, descriptors_2) -> float:
        matches = self.orb_matcher.match(descriptors_1, descriptors_2)

        return self.max_dist(matches, self.threeshold_distance_filter(matches))

    # ==================== ------ MERGING ------- ====================

    @staticmethod
    def threeshold_distance_filter(matches: List) -> List:
        dist_th = 64
        good = []

        for curr_matches in matches:
            if curr_matches.distance < dist_th:
                good.append(curr_matches)

        return good

    @staticmethod
    def max_dist(all_matches: List, good_matches: List) -> float:
        return 1 - len(good_matches) / (max(len(all_matches), len(all_matches)))

    # ==================== ------ DECISIONS ------- ====================

    def compute_decision_from_distance(self, algo_conf: feature_extractor_conf.Algo_conf, dist: float) -> sd.DecisionTypes:
        # From a distance between orb distance, gives a decision : is it a match or not ? Or maybe ?

        if dist <= algo_conf.get('threshold_maybe'):
            # It's a YES ! :)
            return sd.DecisionTypes.YES
        elif dist <= algo_conf.get('threshold_no'):
            # It's a MAYBE :/
            return sd.DecisionTypes.MAYBE
        else:
            # It's a NO :(
            return sd.DecisionTypes.NO
